from datetime import date
from typing import Any

from sqlalchemy import func, select, true
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.models import Exercise, ExerciseEntry
from api.app.core.dates import get_user_today
from api.app.services.exercise import get_owned_exercise
from api.app.services.user import get_allowed_user_by_identity


class ExerciseArchivedError(Exception):
    """Raised when a new entry is requested for an archived exercise."""


class ExerciseEntryNotFoundError(Exception):
    """Raised when an entry does not belong to the resolved user."""


class ExerciseDateInFutureError(Exception):
    """Raised when performed_on is after the user's local today."""


def build_entry_totals_subquery(exercise_id: int):
    repetition = (
        func.unnest(ExerciseEntry.reps)
        .table_valued("value")
        .render_derived()
    )
    return (
        select(
            ExerciseEntry.id.label("id"),
            ExerciseEntry.performed_on.label("performed_on"),
            func.sum(repetition.c.value).label("reps"),
        )
        .select_from(ExerciseEntry)
        .join(repetition, true())
        .where(ExerciseEntry.exercise_id == exercise_id)
        .group_by(ExerciseEntry.id, ExerciseEntry.performed_on)
        .subquery()
    )


async def create_exercise_entry(
    session: AsyncSession,
    provider: str,
    external_id: str,
    exercise_id: int,
    reps: list[int],
    performed_on: date,
) -> ExerciseEntry:
    async with session.begin():
        user = await get_allowed_user_by_identity(session, provider, external_id)
        if performed_on > get_user_today(user.timezone):
            raise ExerciseDateInFutureError
        exercise = await get_owned_exercise(session, exercise_id, user.id)
        if exercise.is_archived:
            raise ExerciseArchivedError

        entry = ExerciseEntry(
            exercise_id=exercise.id,
            reps=reps,
            performed_on=performed_on,
        )
        session.add(entry)
        await session.flush()
        return entry


async def list_exercise_entries(
    session: AsyncSession,
    provider: str,
    external_id: str,
    exercise_id: int,
    from_date: date | None,
    to_date: date | None,
    limit: int,
    offset: int,
) -> list[ExerciseEntry]:
    async with session.begin():
        user = await get_allowed_user_by_identity(session, provider, external_id)
        await get_owned_exercise(session, exercise_id, user.id)

        statement = select(ExerciseEntry).where(
            ExerciseEntry.exercise_id == exercise_id
        )
        if from_date is not None:
            statement = statement.where(ExerciseEntry.performed_on >= from_date)
        if to_date is not None:
            statement = statement.where(ExerciseEntry.performed_on <= to_date)

        statement = statement.order_by(
            ExerciseEntry.performed_on.desc(),
            ExerciseEntry.created_at.desc(),
        ).limit(limit).offset(offset)
        return list((await session.scalars(statement)).all())


async def update_exercise_entry(
    session: AsyncSession,
    provider: str,
    external_id: str,
    entry_id: int,
    changes: dict[str, Any],
) -> ExerciseEntry:
    async with session.begin():
        user = await get_allowed_user_by_identity(session, provider, external_id)
        performed_on = changes.get("performed_on")
        if (
            isinstance(performed_on, date)
            and performed_on > get_user_today(user.timezone)
        ):
            raise ExerciseDateInFutureError
        entry = await _get_owned_entry(session, entry_id, user.id)
        for field, value in changes.items():
            setattr(entry, field, value)
        await session.flush()
        return entry


async def delete_exercise_entry(
    session: AsyncSession,
    provider: str,
    external_id: str,
    entry_id: int,
) -> None:
    async with session.begin():
        user = await get_allowed_user_by_identity(session, provider, external_id)
        entry = await _get_owned_entry(session, entry_id, user.id)
        await session.delete(entry)
        await session.flush()


async def _get_owned_entry(
    session: AsyncSession,
    entry_id: int,
    user_id: int,
) -> ExerciseEntry:
    statement = (
        select(ExerciseEntry)
        .join(Exercise)
        .where(
            ExerciseEntry.id == entry_id,
            Exercise.user_id == user_id,
        )
    )
    entry = await session.scalar(statement)
    if entry is None:
        raise ExerciseEntryNotFoundError
    return entry
