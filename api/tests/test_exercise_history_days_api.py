from datetime import date, timedelta
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.models import Exercise, ExerciseEntry, User, UserIdentity


pytestmark = pytest.mark.asyncio


def identity_payload() -> dict[str, str]:
    return {"provider": "test", "external_id": str(uuid4())}


async def create_user(client: AsyncClient) -> dict[str, str]:
    identity = identity_payload()
    response = await client.post("/users/resolve", json=identity)
    assert response.status_code == 201
    return identity


async def create_exercise(client: AsyncClient, identity: dict[str, str]) -> int:
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
) -> None:
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


async def test_history_days_aggregates_sorts_and_limits_to_ten(
    client: AsyncClient,
) -> None:
    identity = await create_user(client)
    exercise_id = await create_exercise(client, identity)
    today = date.today()
    for offset in range(12):
        await create_entry(
            client,
            identity,
            exercise_id,
            [offset + 1],
            today - timedelta(days=offset),
        )
    await create_entry(client, identity, exercise_id, [4], today)

    response = await client.get(
        f"/exercises/{exercise_id}/history-days",
        params=identity,
    )

    assert response.status_code == 200
    days = response.json()
    assert len(days) == 10
    assert days[0] == {
        "date": today.isoformat(),
        "total_reps": 5,
        "entries_count": 2,
    }
    assert [item["date"] for item in days] == [
        (today - timedelta(days=offset)).isoformat() for offset in range(10)
    ]


async def test_history_days_supports_offset(client: AsyncClient) -> None:
    identity = await create_user(client)
    exercise_id = await create_exercise(client, identity)
    today = date.today()
    for offset in range(3):
        await create_entry(
            client, identity, exercise_id, [10], today - timedelta(days=offset)
        )

    response = await client.get(
        f"/exercises/{exercise_id}/history-days",
        params={**identity, "limit": 1, "offset": 1},
    )

    assert response.status_code == 200
    assert response.json()[0]["date"] == (today - timedelta(days=1)).isoformat()


async def test_history_days_enforces_ownership(client: AsyncClient) -> None:
    owner = await create_user(client)
    other = await create_user(client)
    exercise_id = await create_exercise(client, owner)

    response = await client.get(
        f"/exercises/{exercise_id}/history-days",
        params=other,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Exercise not found"}


async def test_banned_user_cannot_get_history_days(
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
        f"/exercises/{exercise_id}/history-days",
        params=identity,
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "User is banned"}
