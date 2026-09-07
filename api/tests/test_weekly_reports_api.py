from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select, update

from api.app.core import dates
from api.app.models import UserIdentity
from api.app.models.weekly_report import WeeklyReport


pytestmark = pytest.mark.asyncio

MONDAY_0900_MOSCOW = datetime(2026, 8, 31, 6, tzinfo=timezone.utc)


async def seed(client, monkeypatch, language="ru", with_data=True, now=MONDAY_0900_MOSCOW):
    monkeypatch.setattr(dates, "get_utc_now", lambda: now)
    identity = dict(provider="telegram", external_id=str(uuid4()))
    assert (await client.post("/users/resolve", json={**identity, "default_language": language})).status_code == 201
    ids = []
    for name in ["Pull-ups", "Squats"]:
        response = await client.post("/exercises", json={**identity, "name": name})
        ids.append(response.json()["id"])
        if with_data:
            response = await client.post("/exercise-entries", json={**identity, "exercise_id": ids[-1],
                                        "performed_on": "2026-08-25", "reps": [10, 20]})
            assert response.status_code == 201
    return identity, ids


async def materialize_all(client):
    cursor = 0
    while True:
        page = (await client.post("/weekly-reports/materialize", params={"after_id": cursor})).json()
        cursor = page["next_cursor"]
        if cursor is None:
            return


async def lease(client, worker_id="worker-a"):
    return (await client.post("/weekly-reports/lease", json={"worker_id": worker_id, "limit": 10})).json()["reports"]


@pytest.mark.parametrize("language", ["ru", "en"])
async def test_materialize_deduplicates_snapshot_and_lease_delivery(client, monkeypatch, language):
    identity, ids = await seed(client, monkeypatch, language)
    await materialize_all(client)
    reports = await lease(client)
    report = next(item for item in reports if item["external_id"] == identity["external_id"])
    assert len(report["exercises"]) == 2
    assert report["language"] == language
    assert report["week_start"] == "2026-08-24"
    assert not any(item["external_id"] == identity["external_id"] for item in await lease(client, "worker-b"))

    assert (await client.post(f"/weekly-reports/{report['id']}/delivery", json={
        "lock_token": report["lock_token"], "status": "sent",
    })).status_code == 204
    saved = await client.get(f"/weekly-reports/{report['id']}", params=identity)
    assert saved.json()["exercises"] == report["exercises"]
    await materialize_all(client)
    assert not any(item["external_id"] == identity["external_id"] for item in await lease(client, "worker-c"))

    for report_id in [None, report["id"]]:
        params = dict(identity)
        if report_id:
            params["report_id"] = report_id
        png = await client.get(f"/exercises/{ids[0]}/weekly-card", params=params)
        assert png.status_code == 200
        assert png.headers["content-type"] == "image/png"


async def test_no_data_no_report(client, monkeypatch):
    identity, _ = await seed(client, monkeypatch, with_data=False)
    await materialize_all(client)
    assert not any(item["external_id"] == identity["external_id"] for item in await lease(client))


async def test_disabled_exercise_is_excluded_from_weekly_report(client, monkeypatch):
    identity, ids = await seed(client, monkeypatch)
    assert (await client.patch(
        f"/exercises/{ids[1]}/weekly-report",
        json={**identity, "weekly_report_enabled": False},
    )).status_code == 200
    await materialize_all(client)
    report = next(item for item in await lease(client) if item["external_id"] == identity["external_id"])
    assert [item["exercise_id"] for item in report["exercises"]] == [ids[0]]


@pytest.mark.parametrize(
    "now",
    [
        datetime(2026, 8, 30, 20, 59, tzinfo=timezone.utc),
        datetime(2026, 8, 31, 5, 59, tzinfo=timezone.utc),
    ],
)
async def test_does_not_materialize_before_monday_0900(client, db_session, monkeypatch, now):
    identity, _ = await seed(client, monkeypatch, now=now)
    await materialize_all(client)
    report_id = await db_session.scalar(select(WeeklyReport.id).join(
        UserIdentity, UserIdentity.user_id == WeeklyReport.user_id,
    ).where(
        UserIdentity.provider == identity["provider"],
        UserIdentity.external_id == identity["external_id"],
    ))
    assert report_id is None


async def test_tuesday_catches_up_and_expired_lease_is_reclaimed(client, db_session, monkeypatch):
    identity, _ = await seed(client, monkeypatch, now=datetime(2026, 9, 1, 7, tzinfo=timezone.utc))
    await materialize_all(client)
    first = next(item for item in await lease(client) if item["external_id"] == identity["external_id"])
    assert first["week_start"] == "2026-08-24"
    await db_session.execute(update(WeeklyReport).where(WeeklyReport.id == first["id"]).values(
        locked_until=MONDAY_0900_MOSCOW - timedelta(seconds=1),
    ))
    await db_session.commit()
    second = next(item for item in await lease(client, "worker-b") if item["external_id"] == identity["external_id"])
    assert second["id"] == first["id"]
    assert second["lock_token"] != first["lock_token"]
    assert (await client.post(f"/weekly-reports/{first['id']}/delivery", json={
        "lock_token": first["lock_token"], "status": "sent",
    })).status_code == 409


async def test_retry_uses_lease_token_and_stops_after_max_attempts(client, db_session, monkeypatch):
    identity, _ = await seed(client, monkeypatch)
    await materialize_all(client)
    report = next(item for item in await lease(client) if item["external_id"] == identity["external_id"])
    assert (await client.post(f"/weekly-reports/{report['id']}/delivery", json={
        "lock_token": report["lock_token"], "status": "retry", "retry_after_seconds": 1,
        "error": "temporary network error",
    })).status_code == 204
    saved = await db_session.scalar(select(WeeklyReport).where(WeeklyReport.id == report["id"]))
    assert saved.status == "retry"
    assert saved.last_error == "temporary network error"
    assert saved.attempts == 1
