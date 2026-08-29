from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.models import Exercise, ExerciseEntry, User, UserIdentity


pytestmark = pytest.mark.asyncio


async def setup_exercise(client: AsyncClient, name: str = "Pull-ups"):
    identity = {"provider": "test", "external_id": str(uuid4())}
    assert (await client.post("/users/resolve", json=identity)).status_code == 201
    exercise = (
        await client.post("/exercises", json={**identity, "name": name})
    ).json()
    response = await client.post(
        "/exercise-entries",
        json={
            **identity,
            "exercise_id": exercise["id"],
            "reps": [10, 8],
            "performed_on": "2026-08-01",
        },
    )
    assert response.status_code == 201
    return identity, exercise


async def test_clear_history_keeps_exercise_and_other_data(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    identity, target = await setup_exercise(client)
    other = (
        await client.post("/exercises", json={**identity, "name": "Squats"})
    ).json()
    await client.post(
        "/exercise-entries",
        json={
            **identity,
            "exercise_id": other["id"],
            "reps": [20],
            "performed_on": "2026-08-01",
        },
    )

    response = await client.delete(
        f"/exercises/{target['id']}/history", params=identity
    )

    assert response.status_code == 204
    stats = await client.get(f"/exercises/{target['id']}/stats", params=identity)
    assert stats.json()["all_time_entries"] == 0
    assert stats.json()["total_reps"] == 0
    assert await db_session.get(Exercise, target["id"]) is not None
    assert await db_session.scalar(
        select(func.count(ExerciseEntry.id)).where(
            ExerciseEntry.exercise_id == target["id"]
        )
    ) == 0
    assert await db_session.scalar(
        select(func.count(ExerciseEntry.id)).where(
            ExerciseEntry.exercise_id == other["id"]
        )
    ) == 1


async def test_hard_delete_cascades_entries_and_keeps_other_exercises(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    identity, target = await setup_exercise(client)
    other = (
        await client.post("/exercises", json={**identity, "name": "Squats"})
    ).json()

    response = await client.delete(
        f"/exercises/{target['id']}/permanent", params=identity
    )

    assert response.status_code == 204
    assert await db_session.get(Exercise, target["id"]) is None
    assert await db_session.scalar(
        select(func.count(ExerciseEntry.id)).where(
            ExerciseEntry.exercise_id == target["id"]
        )
    ) == 0
    assert await db_session.get(Exercise, other["id"]) is not None


@pytest.mark.parametrize("operation", ["history", "permanent"])
async def test_destructive_operations_enforce_ownership(
    client: AsyncClient, db_session: AsyncSession, operation: str
) -> None:
    owner, target = await setup_exercise(client)
    stranger = {"provider": "test", "external_id": str(uuid4())}
    await client.post("/users/resolve", json=stranger)

    response = await client.delete(
        f"/exercises/{target['id']}/{operation}", params=stranger
    )

    assert response.status_code == 404
    assert await db_session.get(Exercise, target["id"]) is not None
    assert await db_session.scalar(
        select(func.count(ExerciseEntry.id)).where(
            ExerciseEntry.exercise_id == target["id"]
        )
    ) == 1


@pytest.mark.parametrize("operation", ["history", "permanent"])
async def test_banned_user_cannot_run_destructive_operations(
    client: AsyncClient, db_session: AsyncSession, operation: str
) -> None:
    identity = {"provider": "test", "external_id": str(uuid4())}
    async with db_session.begin():
        user = User(is_banned=True)
        user.identities.append(UserIdentity(**identity))
        exercise = Exercise(name="Pull-ups")
        user.exercises.append(exercise)
        db_session.add(user)
        await db_session.flush()
        exercise_id = exercise.id

    response = await client.delete(
        f"/exercises/{exercise_id}/{operation}", params=identity
    )

    assert response.status_code == 403
    assert await db_session.get(Exercise, exercise_id) is not None
