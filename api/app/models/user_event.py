from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from api.app.models.user import User


EVENT_TYPES = (
    "start",
    "exercise_created",
    "result_added",
    "stats_opened",
    "weekly_report_opened",
    "import_used",
    "export_used",
    "weekly_delivery_failed",
)


class UserEvent(TimestampMixin, Base):
    __tablename__ = "user_events"
    __table_args__ = (
        CheckConstraint(
            "event_type IN (" + ", ".join(f"'{event}'" for event in EVENT_TYPES) + ")",
            name="event_type_known",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)

    user: Mapped["User"] = relationship(back_populates="events")


Index("ix_user_events_created_at", UserEvent.created_at)
Index("ix_user_events_user_id_created_at", UserEvent.user_id, UserEvent.created_at)
