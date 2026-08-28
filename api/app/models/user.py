from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, String, false
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.app.core.dates import DEFAULT_TIMEZONE
from api.app.core.languages import DEFAULT_LANGUAGE
from api.app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from api.app.models.exercise import Exercise
    from api.app.models.user_identity import UserIdentity


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    timezone: Mapped[str] = mapped_column(
        String(255),
        default=DEFAULT_TIMEZONE,
        nullable=False,
    )
    language: Mapped[str] = mapped_column(
        String(2),
        default=DEFAULT_LANGUAGE,
        nullable=False,
    )
    is_banned: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=false(),
        nullable=False,
    )

    identities: Mapped[list["UserIdentity"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    exercises: Mapped[list["Exercise"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
