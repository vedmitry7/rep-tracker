from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.core.exercise_names import normalize_exercise_name
from api.app.models import Exercise, ExerciseEntry
from api.app.services.user import get_allowed_user_by_identity


class ExerciseNotFoundError(Exception):
    """Raised when an exercise does not belong to the resolved user."""


class DuplicateExerciseNameError(Exception):
    """Raised when a user already has an active exercise with this name."""


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
    try:
        async with session.begin():
            user = await get_allowed_user_by_identity(session, provider, external_id)
            if await _active_name_exists(session, user.id, name):
                raise DuplicateExerciseNameError
            exercise = Exercise(user_id=user.id, name=name)
            session.add(exercise)
            await session.flush()
            return exercise
    except IntegrityError as error:
        # The partial unique index closes the race between the friendly check
        # above and concurrent creates.
        raise DuplicateExerciseNameError from error


async def rename_exercise(
    session: AsyncSession,
    provider: str,
    external_id: str,
    exercise_id: int,
    name: str,
) -> Exercise:
    try:
        async with session.begin():
            user = await get_allowed_user_by_identity(session, provider, external_id)
            exercise = await get_owned_exercise(session, exercise_id, user.id)
            if await _active_name_exists(
                session, user.id, name, exclude_exercise_id=exercise.id
            ):
                raise DuplicateExerciseNameError
            exercise.name = name
            await session.flush()
            return exercise
    except IntegrityError as error:
        raise DuplicateExerciseNameError from error


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


async def clear_exercise_history(
    session: AsyncSession,
    provider: str,
    external_id: str,
    exercise_id: int,
) -> None:
    async with session.begin():
        user = await get_allowed_user_by_identity(session, provider, external_id)
        await get_owned_exercise(session, exercise_id, user.id)
        await session.execute(
            delete(ExerciseEntry).where(ExerciseEntry.exercise_id == exercise_id)
        )


async def permanently_delete_exercise(
    session: AsyncSession,
    provider: str,
    external_id: str,
    exercise_id: int,
) -> None:
    async with session.begin():
        user = await get_allowed_user_by_identity(session, provider, external_id)
        exercise = await get_owned_exercise(session, exercise_id, user.id)
        await session.delete(exercise)
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


async def _active_name_exists(
    session: AsyncSession,
    user_id: int,
    name: str,
    *,
    exclude_exercise_id: int | None = None,
) -> bool:
    statement = select(Exercise.id).where(
        Exercise.user_id == user_id,
        Exercise.is_archived.is_(False),
        func.lower(func.btrim(Exercise.name)) == normalize_exercise_name(name),
    )
    if exclude_exercise_id is not None:
        statement = statement.where(Exercise.id != exclude_exercise_id)
    return await session.scalar(statement) is not None
