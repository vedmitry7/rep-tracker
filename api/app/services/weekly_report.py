"""Weekly-report snapshots and a durable PostgreSQL delivery queue."""
from collections import defaultdict
from datetime import date, time, timedelta
from uuid import uuid4

from sqlalchemy import and_, case, func, or_, select, true, update
from sqlalchemy.dialects.postgresql import insert

from api.app.core.dates import get_user_now, get_user_today
from api.app.models import Exercise, ExerciseEntry, User, UserIdentity
from api.app.models.weekly_report import WeeklyReport
from api.app.services.exercise import get_owned_exercise
from api.app.services.exercise_entry import build_entry_totals_subquery
from api.app.services.user import get_allowed_user_by_identity


WEEKLY_REPORT_WEEKDAY = 0
WEEKLY_REPORT_DUE_TIME = time(9, 0)
MAX_DELIVERY_ATTEMPTS = 6
LEASE_DURATION = timedelta(minutes=10)
RETRY_DELAYS = (60, 300, 900, 3600, 21600)


def last_week(today: date) -> date:
    return today - timedelta(days=today.weekday() + 7)


def due_week_start(timezone_name: str) -> date | None:
    """Return the latest completed week once its local Monday 09:00 has passed."""
    now = get_user_now(timezone_name)
    if now.weekday() == 6:
        return None
    if now.weekday() > WEEKLY_REPORT_WEEKDAY:
        return last_week(now.date())
    if now.timetz().replace(tzinfo=None) < WEEKLY_REPORT_DUE_TIME:
        return None
    return last_week(now.date())


def calculate_weekly(days, week_start: date) -> dict | None:
    end = week_start + timedelta(days=6)
    daily = defaultdict(int)
    for day, reps in days:
        if day <= end:
            daily[day] += int(reps)
    if not daily:
        return None
    first = min(daily)
    first -= timedelta(days=first.weekday())
    totals = defaultdict(int)
    for day, reps in daily.items():
        totals[day - timedelta(days=day.weekday())] += reps
    count = (week_start - first).days // 7 + 1
    history = [{"start": (week_start - timedelta(weeks=i)).isoformat(),
                "total": totals[week_start - timedelta(weeks=i)]} for i in range(count)]
    current = history[0]["total"]
    previous = history[1]["total"] if count > 1 else None
    active = [(d, n) for d, n in daily.items() if week_start <= d <= end and n > 0]
    best = max(active, key=lambda item: (item[1], item[0])) if active else None
    delta = current - previous if previous is not None else None
    return dict(total=current, previous=previous, delta=delta,
                percent=delta / previous * 100 if previous else None,
                active_days=len(active),
                best_day={"date": best[0].isoformat(), "reps": best[1]} if best else None,
                history=history)


async def exercise_week(session, exercise, start):
    totals = build_entry_totals_subquery(exercise.id)
    rows = (await session.execute(select(totals.c.performed_on, totals.c.reps)
            .where(totals.c.performed_on < start + timedelta(days=7)))).all()
    result = calculate_weekly(rows, start)
    return dict(exercise_id=exercise.id, name=exercise.name, **result) if result else None


async def build_reports(session, due_users: list[tuple[UserIdentity, User, date]]) -> dict[int, dict]:
    """Build a page of snapshots with one exercise and one totals query, not N+1."""
    if not due_users:
        return {}
    users_by_id = {user.id: user for _, user, _ in due_users}
    starts_by_user_id = {user.id: start for _, user, start in due_users}
    exercises = (await session.scalars(select(Exercise).where(
        Exercise.user_id.in_(users_by_id),
        Exercise.is_archived.is_(False),
        Exercise.weekly_report_enabled.is_(True),
    ).order_by(Exercise.user_id, Exercise.position, Exercise.id))).all()
    exercises_by_user_id = defaultdict(list)
    for exercise in exercises:
        exercises_by_user_id[exercise.user_id].append(exercise)

    daily_by_exercise_id = defaultdict(list)
    if exercises:
        repetition = func.unnest(ExerciseEntry.reps).table_valued("value").render_derived()
        rows = (await session.execute(select(
            ExerciseEntry.exercise_id,
            ExerciseEntry.performed_on,
            func.sum(repetition.c.value).label("reps"),
        ).select_from(ExerciseEntry).join(repetition, true()).where(
            ExerciseEntry.exercise_id.in_([exercise.id for exercise in exercises]),
        ).group_by(ExerciseEntry.exercise_id, ExerciseEntry.performed_on))).all()
        for exercise_id, performed_on, reps in rows:
            daily_by_exercise_id[exercise_id].append((performed_on, reps))

    payloads = {}
    for user_id, user in users_by_id.items():
        start = starts_by_user_id[user_id]
        items = []
        for exercise in exercises_by_user_id[user_id]:
            result = calculate_weekly(daily_by_exercise_id[exercise.id], start)
            if result:
                items.append(dict(exercise_id=exercise.id, name=exercise.name, **result))
        payloads[user_id] = dict(
            week_start=start.isoformat(),
            week_end=(start + timedelta(days=6)).isoformat(),
            language=user.language,
            exercises=items,
        )
    return payloads


async def materialize_reports(session, after_id=0, limit=50):
    """Persist due snapshots. A Tuesday start catches up the latest completed week."""
    async with session.begin():
        identities = (await session.execute(select(UserIdentity, User).join(User).where(
            UserIdentity.provider == "telegram",
            UserIdentity.id > after_id,
            User.is_banned.is_(False),
        ).order_by(UserIdentity.id).limit(limit))).all()
        due_users = [(identity, user, start) for identity, user in identities
                     if (start := due_week_start(user.timezone)) is not None]
        payloads = await build_reports(session, due_users)
        rows = [
            dict(
                id=str(uuid4()),
                user_id=user.id,
                week_start=start,
                status="pending",
                payload=payload,
                attempts=0,
                next_attempt_at=func.now(),
            )
            for _, user, start in due_users
            if (payload := payloads[user.id])["exercises"]
        ]
        if rows:
            await session.execute(insert(WeeklyReport).values(rows).on_conflict_do_nothing(
                index_elements=["user_id", "week_start"],
            ))
        return dict(next_cursor=identities[-1][0].id if len(identities) == limit else None)


async def lease_reports(session, worker_id: str, limit: int):
    """Atomically reserve due reports; SKIP LOCKED makes concurrent workers safe."""
    async with session.begin():
        await session.execute(update(WeeklyReport).where(
            WeeklyReport.status == "processing",
            WeeklyReport.locked_until <= func.now(),
        ).values(
            status=case((WeeklyReport.attempts >= MAX_DELIVERY_ATTEMPTS, "failed"), else_="retry"),
            next_attempt_at=case((WeeklyReport.attempts >= MAX_DELIVERY_ATTEMPTS,
                                  WeeklyReport.next_attempt_at), else_=func.now()),
            locked_until=None,
            lock_token=None,
            locked_by=None,
            last_error=func.coalesce(WeeklyReport.last_error, "Delivery lease expired"),
            updated_at=func.now(),
        ))
        rows = (await session.execute(select(WeeklyReport, UserIdentity.external_id).join(
            UserIdentity,
            and_(
                UserIdentity.user_id == WeeklyReport.user_id,
                UserIdentity.provider == "telegram",
            ),
        ).where(or_(
            WeeklyReport.status == "pending",
            WeeklyReport.status == "retry",
        ), WeeklyReport.next_attempt_at <= func.now()).order_by(
            WeeklyReport.next_attempt_at,
            WeeklyReport.created_at,
        ).with_for_update(skip_locked=True).limit(limit))).all()
        reports = []
        for report, external_id in rows:
            token = uuid4()
            report.status = "processing"
            report.attempts += 1
            report.locked_until = func.now() + LEASE_DURATION
            report.lock_token = token
            report.locked_by = worker_id
            report.updated_at = func.now()
            reports.append(dict(id=report.id, external_id=external_id, lock_token=token,
                                **report.payload))
        await session.flush()
        return reports


def retry_delay(attempts: int, retry_after_seconds: int | None = None) -> int:
    if retry_after_seconds is not None:
        return retry_after_seconds
    return RETRY_DELAYS[min(max(attempts - 1, 0), len(RETRY_DELAYS) - 1)]


async def complete_delivery(session, report_id, lock_token, status, error=None,
                            retry_after_seconds=None):
    """Finish a lease only when this worker still owns it."""
    async with session.begin():
        report = await session.scalar(select(WeeklyReport).where(
            WeeklyReport.id == report_id,
            WeeklyReport.status == "processing",
            WeeklyReport.lock_token == lock_token,
        ).with_for_update())
        if report is None:
            return False
        report.locked_until = None
        report.lock_token = None
        report.locked_by = None
        report.updated_at = func.now()
        if status == "sent":
            report.status = "sent"
            report.sent_at = func.now()
            report.last_error = None
            return True
        report.last_error = error
        if report.attempts >= MAX_DELIVERY_ATTEMPTS:
            report.status = "failed"
        else:
            report.status = "retry"
            report.next_attempt_at = func.now() + timedelta(
                seconds=retry_delay(report.attempts, retry_after_seconds)
            )
        return True


async def get_card_data(session, provider, external_id, exercise_id, report_id=None):
    async with session.begin():
        user = await get_allowed_user_by_identity(session, provider, external_id)
        exercise = await get_owned_exercise(session, exercise_id, user.id)
        if report_id:
            report = await session.scalar(select(WeeklyReport).where(
                WeeklyReport.id == report_id, WeeklyReport.user_id == user.id))
            if report is None:
                return None, user.language
            return next((e for e in report.payload["exercises"]
                         if e["exercise_id"] == exercise_id), None), report.payload["language"]
        return await exercise_week(session, exercise, last_week(get_user_today(user.timezone))), user.language


async def owned_report(session, provider, external_id, report_id):
    user = await get_allowed_user_by_identity(session, provider, external_id)
    return await session.scalar(select(WeeklyReport).where(
        WeeklyReport.id == report_id, WeeklyReport.user_id == user.id))
