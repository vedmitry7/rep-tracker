from datetime import date
from typing import TYPE_CHECKING, Any

from sqlalchemy import BigInteger, CheckConstraint, Date, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from api.app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from api.app.models.exercise import Exercise


class ExerciseEntry(TimestampMixin, Base):
    __tablename__ = "exercise_entries"
    __table_args__ = (
        CheckConstraint("cardinality(reps) > 0", name="reps_not_empty"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reps: Mapped[list[int]] = mapped_column(ARRAY(Integer), nullable=False)
    performed_on: Mapped[date] = mapped_column(Date, nullable=False)

    exercise: Mapped["Exercise"] = relationship(back_populates="exercise_entries")

    @validates("reps")
    def validate_reps(self, _key: str, value: Any) -> list[int]:
        if not isinstance(value, list) or not value:
            raise ValueError("reps must be a non-empty list")
        if any(type(rep) is not int or rep <= 0 for rep in value):
            raise ValueError("every reps value must be a positive integer")
        return value
