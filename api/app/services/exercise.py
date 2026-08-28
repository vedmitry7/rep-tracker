from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.models import Exercise
from api.app.services.user import get_allowed_user_by_identity


class ExerciseNotFoundError(Exception):
    """Raised when an exercise does not belong to the resolved user."""


async def list_exercises(
    session: AsyncSession,
    provider: str,
    external_id: str,
) -> list[Exercise]:
    async with session.begin():
        user = await get_allowed_user_by_identity(session, provider, external_id)
        statement = (
            select(Exercise)
            .where(
                Exercise.user_id == user.id,
                Exercise.is_archived.is_(False),
            )
            .order_by(Exercise.position, Exercise.id)
        )
        return list((await session.scalars(statement)).all())


async def create_exercise(
    session: AsyncSession,
    provider: str,
    external_id: str,
    name: str,
) -> Exercise:
    async with session.begin():
        user = await get_allowed_user_by_identity(session, provider, external_id)
        exercise = Exercise(user_id=user.id, name=name)
        session.add(exercise)
        await session.flush()
        return exercise


async def rename_exercise(
    session: AsyncSession,
    provider: str,
    external_id: str,
    exercise_id: int,
    name: str,
) -> Exercise:
    async with session.begin():
        user = await get_allowed_user_by_identity(session, provider, external_id)
        exercise = await get_owned_exercise(session, exercise_id, user.id)
        exercise.name = name
        await session.flush()
        return exercise


async def archive_exercise(
    session: AsyncSession,
    provider: str,
    external_id: str,
    exercise_id: int,
) -> None:
    async with session.begin():
        user = await get_allowed_user_by_identity(session, provider, external_id)
        exercise = await get_owned_exercise(session, exercise_id, user.id)
        exercise.is_archived = True
        await session.flush()


async def get_owned_exercise(
    session: AsyncSession,
    exercise_id: int,
    user_id: int,
) -> Exercise:
    statement = select(Exercise).where(
        Exercise.id == exercise_id,
        Exercise.user_id == user_id,
    )
    exercise = await session.scalar(statement)
    if exercise is None:
        raise ExerciseNotFoundError
    return exercise
