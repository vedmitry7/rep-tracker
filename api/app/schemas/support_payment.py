from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from api.app.schemas.user import ExternalId, Provider


class SupportInvoiceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: Provider
    external_id: ExternalId
    amount: int = Field(ge=1)


class SupportInvoiceResponse(BaseModel):
    payload: str
    amount: int


class SupportPaymentCheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: Provider
    external_id: ExternalId
    payload: str = Field(min_length=1, max_length=64)
    amount: int = Field(ge=1)
    currency: str = Field(min_length=1, max_length=8)


class SupportPaymentCheckResponse(BaseModel):
    valid: bool


class SupportPaymentCompleteRequest(SupportPaymentCheckRequest):
    telegram_payment_charge_id: str = Field(min_length=1, max_length=255)


class SupportPaymentCompleteResponse(BaseModel):
    newly_completed: bool


class SupportPaymentRefundRequest(BaseModel):
    telegram_payment_charge_id: str = Field(min_length=1, max_length=255)
    refunded_at: datetime
