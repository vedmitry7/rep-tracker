from dataclasses import dataclass
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.services.exercise import get_owned_exercise
from api.app.services.exercise_entry import build_entry_totals_subquery
from api.app.services.user import get_allowed_user_by_identity


@dataclass(frozen=True, slots=True)
class ExerciseHistoryDay:
    date: date
    total_reps: int
    entries_count: int


async def list_exercise_history_days(
    session: AsyncSession,
    provider: str,
    external_id: str,
    exercise_id: int,
    limit: int,
    offset: int,
) -> list[ExerciseHistoryDay]:
    async with session.begin():
        user = await get_allowed_user_by_identity(session, provider, external_id)
        await get_owned_exercise(session, exercise_id, user.id)

        entry_totals = build_entry_totals_subquery(exercise_id)
        rows = (
            await session.execute(
                select(
                    entry_totals.c.performed_on,
                    func.sum(entry_totals.c.reps),
                    func.count(entry_totals.c.id),
                )
                .group_by(entry_totals.c.performed_on)
                .order_by(entry_totals.c.performed_on.desc())
                .limit(limit)
                .offset(offset)
            )
        ).all()

        return [
            ExerciseHistoryDay(
                date=row[0],
                total_reps=int(row[1]),
                entries_count=int(row[2]),
            )
            for row in rows
        ]
