from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.models import Exercise, ExerciseEntry
from api.app.schemas.data_import import ImportDay, ImportDocument, ImportExercise
from api.app.services.user import get_allowed_user_by_identity


class ExportExerciseNotFoundError(Exception):
    """Raised when an export requests a non-active exercise of another user."""


async def export_data(
    session: AsyncSession,
    provider: str,
    external_id: str,
    exercise_ids: list[int],
) -> ImportDocument:
    """Build a version-1 import document from the selected active exercises."""

    async with session.begin():
        user = await get_allowed_user_by_identity(session, provider, external_id)
        exercises = list(
            (
                await session.scalars(
                    select(Exercise)
                    .where(
                        Exercise.user_id == user.id,
                        Exercise.is_archived.is_(False),
                        Exercise.id.in_(exercise_ids),
                    )
                    .order_by(Exercise.position, Exercise.id)
                )
            ).all()
        )
        if len(exercises) != len(exercise_ids):
            raise ExportExerciseNotFoundError

        entries = list(
            (
                await session.scalars(
                    select(ExerciseEntry)
                    .where(ExerciseEntry.exercise_id.in_(exercise_ids))
                    .order_by(
                        ExerciseEntry.exercise_id,
                        ExerciseEntry.performed_on,
                        ExerciseEntry.id,
                    )
                )
            ).all()
        )

    entries_by_exercise: dict[int, dict[object, list[list[int]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for entry in entries:
        entries_by_exercise[entry.exercise_id][entry.performed_on].append(
            list(entry.reps)
        )

    return ImportDocument(
        version=1,
        exercises=[
            ImportExercise(
                name=exercise.name,
                days=[
                    ImportDay(date=performed_on.isoformat(), entries=reps)
                    for performed_on, reps in entries_by_exercise[exercise.id].items()
                ],
            )
            for exercise in exercises
        ],
    )
