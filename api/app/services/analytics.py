from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.models import Exercise, ExerciseEntry, User, UserEvent
from api.app.models.weekly_report import WeeklyReport


@dataclass(frozen=True, slots=True)
class Retention:
    cohort_size: int
    returned_users: int


@dataclass(frozen=True, slots=True)
class AnalyticsSummary:
    period_days: int
    period_started_at: datetime
    generated_at: datetime
    total_users: int
    new_users: int
    active_users: int
    activated_new_users: int
    result_entries: int
    average_entries_per_active_user: float
    feature_opens: dict[str, int]
    locales: dict[str, int]
    retention: dict[str, Retention]
    blocked_users: int
    weekly_delivery_failures: int


async def get_analytics_summary(
    session: AsyncSession,
    *,
    period_days: int,
) -> AnalyticsSummary:
    if period_days not in {1, 7, 30}:
        raise ValueError("period_days must be 1, 7, or 30")

    now = datetime.now(timezone.utc)
    today_started_at = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)
    period_started_at = today_started_at - timedelta(days=period_days - 1)

    total_users = await _count(session, select(func.count()).select_from(User))
    new_users = await _count(
        session,
        select(func.count()).select_from(User).where(User.created_at >= period_started_at),
    )
    active_users = await _count(
        session,
        select(func.count())
        .select_from(User)
        .where(User.last_active_at >= period_started_at),
    )
    result_entries = await _count(
        session,
        select(func.count())
        .select_from(ExerciseEntry)
        .where(ExerciseEntry.created_at >= period_started_at),
    )
    active_result_users = await _count(
        session,
        select(func.count(distinct(Exercise.user_id)))
        .select_from(ExerciseEntry)
        .join(Exercise)
        .where(ExerciseEntry.created_at >= period_started_at),
    )
    activated_new_users = await _count(
        session,
        select(func.count(distinct(User.id)))
        .select_from(User)
        .join(Exercise, Exercise.user_id == User.id)
        .join(ExerciseEntry, ExerciseEntry.exercise_id == Exercise.id)
        .where(User.created_at >= period_started_at),
    )

    feature_rows = await session.execute(
        select(UserEvent.event_type, func.count())
        .where(
            UserEvent.created_at >= period_started_at,
            UserEvent.event_type.in_(
                ("stats_opened", "weekly_report_opened", "import_used", "export_used")
            ),
        )
        .group_by(UserEvent.event_type)
    )
    feature_opens = {
        "stats_opened": 0,
        "weekly_report_opened": 0,
        "import_used": 0,
        "export_used": 0,
    }
    feature_opens.update({event_type: count for event_type, count in feature_rows})

    locale_rows = await session.execute(
        select(User.language, func.count()).group_by(User.language).order_by(User.language)
    )
    locales = {language: count for language, count in locale_rows}

    retention = {
        f"day_{days}": await _retention(session, today_started_at, days)
        for days in (2, 7, 30)
    }
    blocked_users = await _count(
        session,
        select(func.count()).select_from(User).where(User.is_blocked.is_(True)),
    )
    weekly_delivery_failures = await _count(
        session,
        select(func.count())
        .select_from(WeeklyReport)
        .where(
            WeeklyReport.created_at >= period_started_at,
            WeeklyReport.status.in_(("retry", "failed")),
        ),
    )

    return AnalyticsSummary(
        period_days=period_days,
        period_started_at=period_started_at,
        generated_at=now,
        total_users=total_users,
        new_users=new_users,
        active_users=active_users,
        activated_new_users=activated_new_users,
        result_entries=result_entries,
        average_entries_per_active_user=(
            result_entries / active_result_users if active_result_users else 0.0
        ),
        feature_opens=feature_opens,
        locales=locales,
        retention=retention,
        blocked_users=blocked_users,
        weekly_delivery_failures=weekly_delivery_failures,
    )


async def _retention(
    session: AsyncSession,
    today_started_at: datetime,
    days: int,
) -> Retention:
    cohort_started_at = today_started_at - timedelta(days=days)
    cohort_finished_at = cohort_started_at + timedelta(days=1)
    target_finished_at = today_started_at + timedelta(days=1)

    cohort = select(User.id).where(
        User.created_at >= cohort_started_at,
        User.created_at < cohort_finished_at,
    ).subquery()
    cohort_size = await _count(session, select(func.count()).select_from(cohort))
    returned_users = await _count(
        session,
        select(func.count(distinct(UserEvent.user_id))).where(
            UserEvent.user_id.in_(select(cohort.c.id)),
            UserEvent.created_at >= today_started_at,
            UserEvent.created_at < target_finished_at,
        ),
    )
    return Retention(cohort_size=cohort_size, returned_users=returned_users)


async def _count(session: AsyncSession, statement) -> int:
    return int((await session.scalar(statement)) or 0)
