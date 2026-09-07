from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from api.app.db.base import Base, TimestampMixin


class WeeklyReport(TimestampMixin, Base):
    __tablename__ = "weekly_reports"
    __table_args__ = (UniqueConstraint("user_id", "week_start"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    week_start: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lock_token: Mapped[UUID | None] = mapped_column(PostgreSQLUUID(as_uuid=True))
    locked_by: Mapped[str | None] = mapped_column(String(64))
    last_error: Mapped[str | None] = mapped_column(Text)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


Index(
    "ix_weekly_reports_available_delivery",
    WeeklyReport.next_attempt_at,
    WeeklyReport.created_at,
    postgresql_where=WeeklyReport.status.in_(("pending", "retry")),
)
Index(
    "ix_weekly_reports_expired_lease",
    WeeklyReport.locked_until,
    postgresql_where=WeeklyReport.status == "processing",
)
