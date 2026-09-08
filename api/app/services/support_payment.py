from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.models import SupportPayment
from api.app.services.user import get_allowed_user_by_identity

SUPPORT_INVOICE_TTL_HOURS = 24


class InvalidSupportPayment(Exception):
    """The payment does not match a current, single-use invoice."""


@dataclass(frozen=True, slots=True)
class CompletedSupportPayment:
    newly_completed: bool


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def create_invoice(
    session: AsyncSession, provider: str, external_id: str, amount: int
) -> SupportPayment:
    async with session.begin():
        await get_allowed_user_by_identity(session, provider, external_id)
        payment = SupportPayment(
            telegram_user_id=int(external_id),
            amount=amount,
            invoice_payload=f"support:{uuid4()}",
            status="pending",
            expires_at=_now() + timedelta(hours=SUPPORT_INVOICE_TTL_HOURS),
        )
        session.add(payment)
        await session.flush()
        return payment


async def _current_payment(
    session: AsyncSession,
    *,
    telegram_user_id: int,
    payload: str,
    amount: int,
    currency: str,
) -> SupportPayment:
    if currency != "XTR":
        raise InvalidSupportPayment
    payment = await session.scalar(
        select(SupportPayment)
        .where(SupportPayment.invoice_payload == payload)
        .with_for_update()
    )
    if (
        payment is None
        or payment.telegram_user_id != telegram_user_id
        or payment.amount != amount
        or payment.status != "pending"
    ):
        raise InvalidSupportPayment
    if payment.expires_at <= _now():
        payment.status = "expired"
        raise InvalidSupportPayment
    return payment


async def check_invoice(
    session: AsyncSession,
    provider: str,
    external_id: str,
    payload: str,
    amount: int,
    currency: str,
) -> bool:
    async with session.begin():
        await get_allowed_user_by_identity(session, provider, external_id)
        try:
            await _current_payment(
                session,
                telegram_user_id=int(external_id),
                payload=payload,
                amount=amount,
                currency=currency,
            )
        except InvalidSupportPayment:
            return False
    return True


async def complete_payment(
    session: AsyncSession,
    provider: str,
    external_id: str,
    payload: str,
    amount: int,
    currency: str,
    telegram_payment_charge_id: str,
) -> CompletedSupportPayment:
    async with session.begin():
        await get_allowed_user_by_identity(session, provider, external_id)
        if currency != "XTR":
            raise InvalidSupportPayment
        existing = await session.scalar(
            select(SupportPayment).where(
                SupportPayment.telegram_payment_charge_id == telegram_payment_charge_id
            )
        )
        if existing is not None:
            if (
                existing.invoice_payload == payload
                and existing.telegram_user_id == int(external_id)
                and existing.amount == amount
                and existing.status == "succeeded"
            ):
                return CompletedSupportPayment(newly_completed=False)
            raise InvalidSupportPayment
        # Locking the invoice makes a duplicate delivery wait until the first
        # completion is visible, then return the same idempotent result.
        payment = await session.scalar(
            select(SupportPayment)
            .where(SupportPayment.invoice_payload == payload)
            .with_for_update()
        )
        if (
            payment is None
            or payment.telegram_user_id != int(external_id)
            or payment.amount != amount
        ):
            raise InvalidSupportPayment
        if payment.status == "succeeded":
            if payment.telegram_payment_charge_id == telegram_payment_charge_id:
                return CompletedSupportPayment(newly_completed=False)
            raise InvalidSupportPayment
        if payment.status != "pending" or payment.expires_at <= _now():
            if payment.status == "pending":
                payment.status = "expired"
            raise InvalidSupportPayment
        payment.telegram_payment_charge_id = telegram_payment_charge_id
        payment.status = "succeeded"
        payment.paid_at = _now()
        await session.flush()
        return CompletedSupportPayment(newly_completed=True)


async def mark_refunded(
    session: AsyncSession, telegram_payment_charge_id: str, refunded_at: datetime
) -> None:
    """Persist a refund only after Bot.refund_star_payment has succeeded."""
    async with session.begin():
        payment = await session.scalar(
            select(SupportPayment)
            .where(SupportPayment.telegram_payment_charge_id == telegram_payment_charge_id)
            .with_for_update()
        )
        if payment is None or payment.status != "succeeded":
            raise InvalidSupportPayment
        payment.status = "refunded"
        payment.refunded_at = refunded_at
