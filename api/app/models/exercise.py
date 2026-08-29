from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    false,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from api.app.models.exercise_entry import ExerciseEntry
    from api.app.models.user import User


class Exercise(TimestampMixin, Base):
    __tablename__ = "exercises"
    __table_args__ = (
        CheckConstraint("btrim(name) <> ''", name="name_not_blank"),
        CheckConstraint("position >= 0", name="position_non_negative"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )
    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=false(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="exercises")
    exercise_entries: Mapped[list["ExerciseEntry"]] = relationship(
        back_populates="exercise",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


Index(
    "uq_exercises_user_active_name_normalized",
    Exercise.user_id,
    func.lower(func.btrim(Exercise.name)),
    unique=True,
    postgresql_where=Exercise.is_archived.is_(False),
)
