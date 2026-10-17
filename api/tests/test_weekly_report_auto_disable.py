from datetime import date, datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select, update

from api.app.core import dates
from api.app.models import Exercise, UserIdentity
from api.app.models.weekly_report import WeeklyReport
from api.app.services.weekly_report import should_auto_disable


pytestmark = pytest.mark.asyncio

MONDAY_0900_MOSCOW = datetime(2026, 8, 31, 6, tzinfo=timezone.utc)
MONDAY_0900_MOSCOW_2 = datetime(2026, 9, 7, 6, tzinfo=timezone.utc)
OLD_ENOUGH = datetime(2026, 7, 1, tzinfo=timezone.utc)


async def seed_user(client, monkeypatch, *, now=MONDAY_0900_MOSCOW, language="ru"):
    monkeypatch.setattr(dates, "get_utc_now", lambda: now)
    identity = dict(provider="telegram", external_id=str(uuid4()))
    assert (await client.post("/users/resolve", json={
        **identity, "default_language": language,
    })).status_code == 201
    return identity


async def add_exercise(client, identity, name, *, enabled_at=OLD_ENOUGH, entries=()):
    response = await client.post("/exercises", json={**identity, "name": name})
    assert response.status_code == 201
    exercise_id = response.json()["id"]
    for performed_on, reps in entries:
        assert (await client.post("/exercise-entries", json={
            **identity, "exercise_id": exercise_id,
            "performed_on": performed_on, "reps": reps,
        })).status_code == 201
    return exercise_id


async def set_enabled_at(db_session, exercise_id, moment):
    await db_session.execute(
        update(Exercise).where(Exercise.id == exercise_id).values(
            weekly_report_enabled_at=moment,
        )
    )
    await db_session.commit()


async def materialize_all(client):
    cursor = 0
    while True:
        page = (await client.post(
            "/weekly-reports/materialize", params={"after_id": cursor},
        )).json()
        cursor = page["next_cursor"]
        if cursor is None:
            return


async def lease(client, worker_id="worker-a"):
    return (await client.post(
        "/weekly-reports/lease", json={"worker_id": worker_id, "limit": 10},
    )).json()["reports"]


async def reports_for(client, identity, worker_id="worker-a"):
    return [item for item in await lease(client, worker_id)
            if item["external_id"] == identity["external_id"]]


async def exercise_enabled(db_session, exercise_id):
    enabled = await db_session.scalar(
        select(Exercise.weekly_report_enabled).where(Exercise.id == exercise_id)
    )
    await db_session.commit()
    return enabled


async def stored_report(db_session, identity):
    user_id = select(UserIdentity.user_id).where(
        UserIdentity.provider == identity["provider"],
        UserIdentity.external_id == identity["external_id"],
    ).scalar_subquery()
    report = await db_session.scalar(
        select(WeeklyReport).where(WeeklyReport.user_id == user_id)
    )
    await db_session.commit()
    return report


async def test_two_empty_full_weeks_disable_and_notify_once(client, db_session, monkeypatch):
    identity = await seed_user(client, monkeypatch)
    exercise_id = await add_exercise(client, identity, "Pull-ups")
    await set_enabled_at(db_session, exercise_id, OLD_ENOUGH)

    await materialize_all(client)

    reports = await reports_for(client, identity)
    assert len(reports) == 1
    report = reports[0]
    assert report["exercises"] == []
    assert [item["exercise_id"] for item in report["disabled_exercises"]] == [exercise_id]
    assert report["disabled_exercises"][0]["name"] == "Pull-ups"
    assert await exercise_enabled(db_session, exercise_id) is False

    saved = await client.get(f"/weekly-reports/{report['id']}", params=identity)
    assert saved.json()["disabled_exercises"] == report["disabled_exercises"]

    assert (await client.post(f"/weekly-reports/{report['id']}/delivery", json={
        "lock_token": report["lock_token"], "status": "sent",
    })).status_code == 204
    await materialize_all(client)
    assert await reports_for(client, identity, "worker-b") == []


async def test_single_empty_week_is_not_enough(client, db_session, monkeypatch):
    identity = await seed_user(client, monkeypatch)
    exercise_id = await add_exercise(
        client, identity, "Pull-ups", entries=[("2026-08-18", [10])],
    )
    await set_enabled_at(db_session, exercise_id, OLD_ENOUGH)

    await materialize_all(client)

    reports = await reports_for(client, identity)
    assert len(reports) == 1
    assert reports[0]["disabled_exercises"] == []
    assert [item["exercise_id"] for item in reports[0]["exercises"]] == [exercise_id]
    assert await exercise_enabled(db_session, exercise_id) is True


async def test_activity_in_the_second_week_resets_the_sequence(client, db_session, monkeypatch):
    identity = await seed_user(client, monkeypatch)
    exercise_id = await add_exercise(
        client, identity, "Pull-ups", entries=[("2026-08-25", [10])],
    )
    await set_enabled_at(db_session, exercise_id, OLD_ENOUGH)

    await materialize_all(client)

    reports = await reports_for(client, identity)
    assert reports and reports[0]["disabled_exercises"] == []
    assert await exercise_enabled(db_session, exercise_id) is True


async def test_new_exercise_gets_two_full_weeks(client, db_session, monkeypatch):
    identity = await seed_user(client, monkeypatch)
    exercise_id = await add_exercise(client, identity, "Pull-ups")
    await set_enabled_at(db_session, exercise_id, MONDAY_0900_MOSCOW)

    await materialize_all(client)

    assert await reports_for(client, identity) == []
    assert await exercise_enabled(db_session, exercise_id) is True


async def test_mid_week_creation_waits_two_full_weeks(client, db_session, monkeypatch):
    identity = await seed_user(client, monkeypatch)
    exercise_id = await add_exercise(client, identity, "Pull-ups")
    await set_enabled_at(db_session, exercise_id, datetime(2026, 8, 19, tzinfo=timezone.utc))

    await materialize_all(client)
    assert await reports_for(client, identity) == []
    assert await exercise_enabled(db_session, exercise_id) is True

    monkeypatch.setattr(dates, "get_utc_now", lambda: MONDAY_0900_MOSCOW_2)
    await materialize_all(client)

    reports = await reports_for(client, identity, "worker-b")
    assert reports and [item["exercise_id"] for item in reports[0]["disabled_exercises"]] == [exercise_id]
    assert await exercise_enabled(db_session, exercise_id) is False


async def test_old_history_does_not_prevent_disable(client, db_session, monkeypatch):
    identity = await seed_user(client, monkeypatch)
    exercise_id = await add_exercise(
        client, identity, "Pull-ups", entries=[("2026-08-04", [10])],
    )
    await set_enabled_at(db_session, exercise_id, OLD_ENOUGH)

    await materialize_all(client)

    reports = await reports_for(client, identity)
    assert reports and [item["exercise_id"] for item in reports[0]["disabled_exercises"]] == [exercise_id]
    assert await exercise_enabled(db_session, exercise_id) is False


async def test_multiple_disables_are_combined_and_others_keep_reporting(
    client, db_session, monkeypatch,
):
    identity = await seed_user(client, monkeypatch)
    first = await add_exercise(client, identity, "Pull-ups")
    second = await add_exercise(client, identity, "Squats")
    active = await add_exercise(
        client, identity, "Push-ups", entries=[("2026-08-25", [10])],
    )
    for exercise_id in (first, second, active):
        await set_enabled_at(db_session, exercise_id, OLD_ENOUGH)

    await materialize_all(client)

    reports = await reports_for(client, identity)
    assert len(reports) == 1
    disabled_ids = {item["exercise_id"] for item in reports[0]["disabled_exercises"]}
    assert disabled_ids == {first, second}
    assert [item["exercise_id"] for item in reports[0]["exercises"]] == [active]
    assert await exercise_enabled(db_session, first) is False
    assert await exercise_enabled(db_session, active) is True


async def test_manual_disable_is_not_announced(client, db_session, monkeypatch):
    identity = await seed_user(client, monkeypatch)
    exercise_id = await add_exercise(client, identity, "Pull-ups")
    await set_enabled_at(db_session, exercise_id, OLD_ENOUGH)
    assert (await client.patch(f"/exercises/{exercise_id}/weekly-report", json={
        **identity, "weekly_report_enabled": False,
    })).status_code == 200

    await materialize_all(client)

    assert await reports_for(client, identity) == []
    assert await stored_report(db_session, identity) is None


async def test_reenabled_exercise_is_not_disabled_again_immediately(
    client, db_session, monkeypatch,
):
    identity = await seed_user(client, monkeypatch)
    exercise_id = await add_exercise(client, identity, "Pull-ups")
    await set_enabled_at(db_session, exercise_id, OLD_ENOUGH)
    await materialize_all(client)
    report = (await reports_for(client, identity))[0]
    assert (await client.post(f"/weekly-reports/{report['id']}/delivery", json={
        "lock_token": report["lock_token"], "status": "sent",
    })).status_code == 204

    assert (await client.patch(f"/exercises/{exercise_id}/weekly-report", json={
        **identity, "weekly_report_enabled": True,
    })).status_code == 200
    await materialize_all(client)

    assert await exercise_enabled(db_session, exercise_id) is True
    assert await reports_for(client, identity, "worker-b") == []


class FakeExercise:
    def __init__(self, created_at, enabled_at):
        self.created_at = created_at
        self.weekly_report_enabled_at = enabled_at


class FakeUser:
    timezone = "Europe/Moscow"


async def test_should_auto_disable_unit():
    user = FakeUser()
    old = datetime(2026, 6, 1, tzinfo=timezone.utc)
    exercise = FakeExercise(created_at=old, enabled_at=None)
    week_start = date(2026, 8, 24)

    assert should_auto_disable(exercise, user, [], week_start) is True

    started = FakeExercise(created_at=old, enabled_at=datetime(2026, 8, 25, tzinfo=timezone.utc))
    assert should_auto_disable(started, user, [], week_start) is False

    one_active = [(date(2026, 8, 25), 5)]
    assert should_auto_disable(exercise, user, one_active, week_start) is False

    previous_active = [(date(2026, 8, 18), 5)]
    assert should_auto_disable(exercise, user, previous_active, week_start) is False
