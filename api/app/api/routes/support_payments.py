from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.db.session import get_db_session
from api.app.schemas.support_payment import (
    SupportInvoiceRequest,
    SupportInvoiceResponse,
    SupportPaymentCheckRequest,
    SupportPaymentCheckResponse,
    SupportPaymentCompleteRequest,
    SupportPaymentCompleteResponse,
    SupportPaymentRefundRequest,
)
from api.app.services.support_payment import (
    InvalidSupportPayment,
    check_invoice,
    complete_payment,
    create_invoice,
    mark_refunded,
)
from api.app.services.user import UserBannedError, UserNotFoundError


router = APIRouter(prefix="/support-payments", tags=["support payments"])
Session = Annotated[AsyncSession, Depends(get_db_session)]


def _payment_error(error: Exception) -> HTTPException:
    if isinstance(error, UserBannedError):
        return HTTPException(status.HTTP_403_FORBIDDEN, "User is banned")
    if isinstance(error, UserNotFoundError):
        return HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid support payment")


@router.post("/invoices", response_model=SupportInvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_support_invoice(payload: SupportInvoiceRequest, session: Session) -> SupportInvoiceResponse:
    try:
        payment = await create_invoice(session, payload.provider, payload.external_id, payload.amount)
    except (InvalidSupportPayment, UserBannedError, UserNotFoundError) as error:
        raise _payment_error(error) from error
    return SupportInvoiceResponse(payload=payment.invoice_payload, amount=payment.amount)


@router.post("/check", response_model=SupportPaymentCheckResponse)
async def check_support_payment(payload: SupportPaymentCheckRequest, session: Session) -> SupportPaymentCheckResponse:
    try:
        valid = await check_invoice(session, payload.provider, payload.external_id, payload.payload, payload.amount, payload.currency)
    except (UserBannedError, UserNotFoundError) as error:
        raise _payment_error(error) from error
    return SupportPaymentCheckResponse(valid=valid)


@router.post("/complete", response_model=SupportPaymentCompleteResponse)
async def complete_support_payment(payload: SupportPaymentCompleteRequest, session: Session) -> SupportPaymentCompleteResponse:
    try:
        result = await complete_payment(session, payload.provider, payload.external_id, payload.payload, payload.amount, payload.currency, payload.telegram_payment_charge_id)
    except (InvalidSupportPayment, UserBannedError, UserNotFoundError) as error:
        raise _payment_error(error) from error
    return SupportPaymentCompleteResponse(newly_completed=result.newly_completed)


@router.post("/refund", status_code=status.HTTP_204_NO_CONTENT)
async def record_support_refund(payload: SupportPaymentRefundRequest, session: Session) -> None:
    try:
        await mark_refunded(session, payload.telegram_payment_charge_id, payload.refunded_at)
    except InvalidSupportPayment as error:
        raise _payment_error(error) from error
