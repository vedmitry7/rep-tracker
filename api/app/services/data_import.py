from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.core.dates import get_user_today
from api.app.models import Exercise, ExerciseEntry, User
from api.app.schemas.data_import import (
    ImportDocument,
    ImportPreviewResponse,
    ImportResultResponse,
    ImportStrategy,
)
from api.app.services.user import get_allowed_user_by_identity


class ImportDateInFutureError(Exception):
    """Raised when the document contains a future local training date."""


@dataclass(frozen=True, slots=True)
class ImportPlan:
    preview: ImportPreviewResponse
    matches: dict[int, Exercise]


def normalize_exercise_name(name: str) -> str:
    return name.strip().casefold()


async def preview_data_import(
    session: AsyncSession,
    provider: str,
    external_id: str,
    document: ImportDocument,
) -> ImportPreviewResponse:
    async with session.begin():
        user = await get_allowed_user_by_identity(session, provider, external_id)
        return (await _build_import_plan(session, user, document)).preview


async def apply_data_import(
    session: AsyncSession,
    provider: str,
    external_id: str,
    document: ImportDocument,
    strategy: ImportStrategy,
) -> ImportResultResponse:
    async with session.begin():
        user = await get_allowed_user_by_identity(session, provider, external_id)
        plan = await _build_import_plan(session, user, document)

        matched_ids = {exercise.id for exercise in plan.matches.values()}
        if strategy is ImportStrategy.REPLACE and matched_ids:
            await session.execute(
                delete(ExerciseEntry).where(
                    ExerciseEntry.exercise_id.in_(matched_ids)
                )
            )

        exercises_created = 0
        for index, imported_exercise in enumerate(document.exercises):
            exercise = plan.matches.get(index)
            if exercise is None:
                exercise = Exercise(user_id=user.id, name=imported_exercise.name)
                session.add(exercise)
                await session.flush()
                exercises_created += 1

            for day in imported_exercise.days:
                session.add_all(
                    ExerciseEntry(
                        exercise_id=exercise.id,
                        reps=list(reps),
                        performed_on=day.date,
                    )
                    for reps in day.entries
                )

        await session.flush()
        return ImportResultResponse(
            strategy=strategy,
            exercises_created=exercises_created,
            existing_exercises_updated=len(matched_ids),
            entries_imported=plan.preview.entries_count,
            total_reps_imported=plan.preview.total_reps,
        )


async def _build_import_plan(
    session: AsyncSession,
    user: User,
    document: ImportDocument,
) -> ImportPlan:
    active_exercises = list(
        (
            await session.scalars(
                select(Exercise)
                .where(
                    Exercise.user_id == user.id,
                    Exercise.is_archived.is_(False),
                )
                .order_by(Exercise.position, Exercise.id)
            )
        ).all()
    )
    existing_by_name: dict[str, Exercise] = {}
    for exercise in active_exercises:
        existing_by_name.setdefault(normalize_exercise_name(exercise.name), exercise)

    today = get_user_today(user.timezone)
    dates = [
        day.date
        for imported_exercise in document.exercises
        for day in imported_exercise.days
    ]
    if any(performed_on > today for performed_on in dates):
        raise ImportDateInFutureError

    matches: dict[int, Exercise] = {}
    new_names: list[str] = []
    existing_names: list[str] = []
    seen_existing_ids: set[int] = set()
    for index, imported_exercise in enumerate(document.exercises):
        match = existing_by_name.get(normalize_exercise_name(imported_exercise.name))
        if match is None:
            new_names.append(imported_exercise.name)
            continue
        matches[index] = match
        if match.id not in seen_existing_ids:
            existing_names.append(match.name)
            seen_existing_ids.add(match.id)

    entries_count = sum(
        len(day.entries)
        for imported_exercise in document.exercises
        for day in imported_exercise.days
    )
    total_reps = sum(
        sum(reps)
        for imported_exercise in document.exercises
        for day in imported_exercise.days
        for reps in day.entries
    )
    return ImportPlan(
        preview=ImportPreviewResponse(
            exercises_count=len(document.exercises),
            entries_count=entries_count,
            total_reps=total_reps,
            date_from=min(dates),
            date_to=max(dates),
            new_exercises=new_names,
            existing_exercises=existing_names,
        ),
        matches=matches,
    )
