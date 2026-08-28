from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.models import Exercise, ExerciseEntry, User, UserIdentity
from api.app.core import dates


pytestmark = pytest.mark.asyncio


def identity_payload() -> dict[str, str]:
    return {"provider": "test", "external_id": str(uuid4())}


async def create_user(client: AsyncClient) -> dict[str, str]:
    identity = identity_payload()
    response = await client.post("/users/resolve", json=identity)
    assert response.status_code == 201
    return identity


async def create_exercise(
    client: AsyncClient,
    identity: dict[str, str],
) -> int:
    response = await client.post(
        "/exercises",
        json={**identity, "name": "Pull-ups"},
    )
    assert response.status_code == 201
    return int(response.json()["id"])


async def create_entry(
    client: AsyncClient,
    identity: dict[str, str],
    exercise_id: int,
    reps: list[int],
    performed_on: date,
) -> dict[str, object]:
    response = await client.post(
        "/exercise-entries",
        json={
            **identity,
            "exercise_id": exercise_id,
            "reps": reps,
            "performed_on": performed_on.isoformat(),
        },
    )
    assert response.status_code == 201
    return response.json()


async def test_empty_exercise_stats(client: AsyncClient) -> None:
    identity = await create_user(client)
    exercise_id = await create_exercise(client, identity)

    response = await client.get(
        f"/exercises/{exercise_id}/stats",
        params=identity,
    )

    assert response.status_code == 200
    assert response.json() == {
        "today": date.today().isoformat(),
        "total_reps": 0,
        "today_reps": 0,
        "last_7_days_reps": 0,
        "last_30_days_reps": 0,
        "all_time_entries": 0,
        "active_days": 0,
        "best_day": None,
        "last_entry": None,
    }


async def test_stats_aggregate_calendar_windows_days_and_entries(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    identity = await create_user(client)
    exercise_id = await create_exercise(client, identity)
    today = date.today()

    first_today = await create_entry(
        client, identity, exercise_id, [10, 9], today
    )
    last_today = await create_entry(client, identity, exercise_id, [5], today)
    await create_entry(client, identity, exercise_id, [20], today - timedelta(days=6))
    await create_entry(client, identity, exercise_id, [30], today - timedelta(days=7))
    await create_entry(client, identity, exercise_id, [40], today - timedelta(days=29))
    await create_entry(
        client, identity, exercise_id, [25, 25], today - timedelta(days=20)
    )
    await create_entry(client, identity, exercise_id, [50], today - timedelta(days=30))

    async with db_session.begin():
        first_today_model = await db_session.get(ExerciseEntry, first_today["id"])
        last_today_model = await db_session.get(ExerciseEntry, last_today["id"])
        assert first_today_model is not None
        assert last_today_model is not None
        first_today_model.created_at = datetime(2026, 1, 2, tzinfo=timezone.utc)
        last_today_model.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)

    response = await client.get(
        f"/exercises/{exercise_id}/stats",
        params=identity,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_reps"] == 214
    assert body["today_reps"] == 24
    assert body["last_7_days_reps"] == 44
    assert body["last_30_days_reps"] == 164
    assert body["all_time_entries"] == 7
    assert body["active_days"] == 6
    assert body["best_day"] == {
        "date": (today - timedelta(days=20)).isoformat(),
        "reps": 50,
    }
    assert body["last_entry"]["id"] == first_today["id"]
    assert body["last_entry"]["reps"] == [10, 9]


async def test_best_day_sums_multiple_entries_and_prefers_fresher_tie(
    client: AsyncClient,
) -> None:
    identity = await create_user(client)
    exercise_id = await create_exercise(client, identity)
    today = date.today()
    older = today - timedelta(days=3)
    fresher = today - timedelta(days=1)
    await create_entry(client, identity, exercise_id, [10, 15], older)
    await create_entry(client, identity, exercise_id, [20], older)
    await create_entry(client, identity, exercise_id, [45], fresher)

    response = await client.get(
        f"/exercises/{exercise_id}/stats",
        params=identity,
    )

    assert response.json()["best_day"] == {
        "date": fresher.isoformat(),
        "reps": 45,
    }


async def test_stats_of_another_users_exercise_returns_not_found(
    client: AsyncClient,
) -> None:
    owner = await create_user(client)
    other = await create_user(client)
    exercise_id = await create_exercise(client, owner)

    response = await client.get(
        f"/exercises/{exercise_id}/stats",
        params=other,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Exercise not found"}


async def test_banned_user_cannot_get_stats(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    identity = identity_payload()
    async with db_session.begin():
        user = User(is_banned=True)
        user.identities.append(UserIdentity(**identity))
        exercise = Exercise(name="Pull-ups")
        exercise.exercise_entries.append(
            ExerciseEntry(reps=[10], performed_on=date.today())
        )
        user.exercises.append(exercise)
        db_session.add(user)
        await db_session.flush()
        exercise_id = exercise.id

    response = await client.get(
        f"/exercises/{exercise_id}/stats",
        params=identity,
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "User is banned"}


async def test_stats_windows_use_each_users_timezone(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    identities = {
        "moscow": identity_payload(),
        "new_york": identity_payload(),
    }
    timezones = {
        "moscow": "Europe/Moscow",
        "new_york": "America/New_York",
    }
    exercise_ids: dict[str, int] = {}
    for key, identity in identities.items():
        response = await client.post(
            "/users/resolve",
            json={**identity, "default_timezone": timezones[key]},
        )
        assert response.status_code == 201
        exercise_ids[key] = await create_exercise(client, identity)

    async with db_session.begin():
        db_session.add_all(
            [
                ExerciseEntry(
                    exercise_id=exercise_ids["moscow"],
                    reps=[10],
                    performed_on=date(2026, 8, 28),
                ),
                ExerciseEntry(
                    exercise_id=exercise_ids["moscow"],
                    reps=[20],
                    performed_on=date(2026, 8, 22),
                ),
                ExerciseEntry(
                    exercise_id=exercise_ids["moscow"],
                    reps=[40],
                    performed_on=date(2026, 8, 21),
                ),
                ExerciseEntry(
                    exercise_id=exercise_ids["moscow"],
                    reps=[80],
                    performed_on=date(2026, 8, 29),
                ),
                ExerciseEntry(
                    exercise_id=exercise_ids["new_york"],
                    reps=[11],
                    performed_on=date(2026, 8, 27),
                ),
                ExerciseEntry(
                    exercise_id=exercise_ids["new_york"],
                    reps=[22],
                    performed_on=date(2026, 8, 21),
                ),
                ExerciseEntry(
                    exercise_id=exercise_ids["new_york"],
                    reps=[44],
                    performed_on=date(2026, 8, 20),
                ),
            ]
        )

    monkeypatch.setattr(
        dates,
        "get_utc_now",
        lambda: datetime(2026, 8, 27, 22, 30, tzinfo=timezone.utc),
    )

    moscow = await client.get(
        f"/exercises/{exercise_ids['moscow']}/stats",
        params=identities["moscow"],
    )
    new_york = await client.get(
        f"/exercises/{exercise_ids['new_york']}/stats",
        params=identities["new_york"],
    )

    assert moscow.json()["today"] == "2026-08-28"
    assert moscow.json()["today_reps"] == 10
    assert moscow.json()["last_7_days_reps"] == 30
    assert moscow.json()["last_30_days_reps"] == 70
    assert new_york.json()["today"] == "2026-08-27"
    assert new_york.json()["today_reps"] == 11
    assert new_york.json()["last_7_days_reps"] == 33
    assert new_york.json()["last_30_days_reps"] == 77
