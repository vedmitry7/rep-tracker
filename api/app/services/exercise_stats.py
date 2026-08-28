from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.core.dates import get_user_today
from api.app.models import ExerciseEntry
from api.app.services.exercise import get_owned_exercise
from api.app.services.exercise_entry import build_entry_totals_subquery
from api.app.services.user import get_allowed_user_by_identity


@dataclass(frozen=True, slots=True)
class BestDay:
    date: date
    reps: int


@dataclass(frozen=True, slots=True)
class ExerciseStats:
    today: date
    total_reps: int
    today_reps: int
    last_7_days_reps: int
    last_30_days_reps: int
    all_time_entries: int
    active_days: int
    best_day: BestDay | None
    last_entry: ExerciseEntry | None


async def get_exercise_stats(
    session: AsyncSession,
    provider: str,
    external_id: str,
    exercise_id: int,
) -> ExerciseStats:
    async with session.begin():
        user = await get_allowed_user_by_identity(session, provider, external_id)
        await get_owned_exercise(session, exercise_id, user.id)

        today = get_user_today(user.timezone)
        entry_totals = build_entry_totals_subquery(exercise_id)
        summary = (
            await session.execute(
                select(
                    func.coalesce(func.sum(entry_totals.c.reps), 0),
                    func.coalesce(
                        func.sum(entry_totals.c.reps).filter(
                            entry_totals.c.performed_on == today
                        ),
                        0,
                    ),
                    func.coalesce(
                        func.sum(entry_totals.c.reps).filter(
                            entry_totals.c.performed_on
                            >= today - timedelta(days=6),
                            entry_totals.c.performed_on <= today,
                        ),
                        0,
                    ),
                    func.coalesce(
                        func.sum(entry_totals.c.reps).filter(
                            entry_totals.c.performed_on
                            >= today - timedelta(days=29),
                            entry_totals.c.performed_on <= today,
                        ),
                        0,
                    ),
                    func.count(entry_totals.c.id),
                    func.count(distinct(entry_totals.c.performed_on)),
                )
            )
        ).one()

        best_day_row = (
            await session.execute(
                select(
                    entry_totals.c.performed_on,
                    func.sum(entry_totals.c.reps).label("reps"),
                )
                .group_by(entry_totals.c.performed_on)
                .order_by(
                    func.sum(entry_totals.c.reps).desc(),
                    entry_totals.c.performed_on.desc(),
                )
                .limit(1)
            )
        ).one_or_none()

        last_entry = await session.scalar(
            select(ExerciseEntry)
            .where(ExerciseEntry.exercise_id == exercise_id)
            .order_by(
                ExerciseEntry.performed_on.desc(),
                ExerciseEntry.created_at.desc(),
                ExerciseEntry.id.desc(),
            )
            .limit(1)
        )

        return ExerciseStats(
            today=today,
            total_reps=int(summary[0]),
            today_reps=int(summary[1]),
            last_7_days_reps=int(summary[2]),
            last_30_days_reps=int(summary[3]),
            all_time_entries=int(summary[4]),
            active_days=int(summary[5]),
            best_day=(
                BestDay(date=best_day_row.performed_on, reps=int(best_day_row.reps))
                if best_day_row is not None
                else None
            ),
            last_entry=last_entry,
        )
