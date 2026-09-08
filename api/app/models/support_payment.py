from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from api.app.db.base import Base, TimestampMixin


class SupportPayment(TimestampMixin, Base):
    """A single-use Telegram Stars invoice and its eventual payment state."""

    __tablename__ = "support_payments"
    __table_args__ = (
        CheckConstraint("amount > 0", name="support_payments_amount_positive"),
        CheckConstraint(
            "status IN ('pending', 'succeeded', 'expired', 'refunded')",
            name="support_payments_status_known",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    amount: Mapped[int] = mapped_column(Integer)
    invoice_payload: Mapped[str] = mapped_column(String(64), unique=True)
    telegram_payment_charge_id: Mapped[str | None] = mapped_column(
        String(255), unique=True
    )
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
