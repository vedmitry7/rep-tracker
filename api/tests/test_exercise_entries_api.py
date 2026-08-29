from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.core.dates import DEFAULT_TIMEZONE, get_user_today
from api.app.models import Exercise, ExerciseEntry, User, UserIdentity
from api.app.schemas.exercise_entry import (
    MAX_REPETITIONS_PER_SET,
    MAX_SETS_PER_ENTRY,
)


pytestmark = pytest.mark.asyncio


def identity_payload() -> dict[str, str]:
    return {
        "provider": "test",
        "external_id": str(uuid4()),
    }


async def create_user(client: AsyncClient) -> dict[str, str]:
    identity = identity_payload()
    response = await client.post("/users/resolve", json=identity)
    assert response.status_code == 201
    return identity


async def create_exercise_for(
    client: AsyncClient,
    identity: dict[str, str],
) -> dict[str, object]:
    response = await client.post(
        "/exercises",
        json={**identity, "name": "Pull-ups"},
    )
    assert response.status_code == 201
    return response.json()


async def create_entry_for(
    client: AsyncClient,
    identity: dict[str, str],
    exercise_id: int,
    reps: list[int] | None = None,
    performed_on: date | None = None,
) -> dict[str, object]:
    response = await client.post(
        "/exercise-entries",
        json={
            **identity,
            "exercise_id": exercise_id,
            "reps": reps or [10],
            "performed_on": (performed_on or date.today()).isoformat(),
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.parametrize("reps", [[10], [10, 9, 8, 7]])
async def test_create_exercise_entry(
    client: AsyncClient,
    reps: list[int],
) -> None:
    identity = await create_user(client)
    exercise = await create_exercise_for(client, identity)

    response = await client.post(
        "/exercise-entries",
        json={
            **identity,
            "exercise_id": exercise["id"],
            "reps": reps,
            "performed_on": date.today().isoformat(),
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": response.json()["id"],
        "exercise_id": exercise["id"],
        "reps": reps,
        "performed_on": date.today().isoformat(),
        "created_at": response.json()["created_at"],
    }
    assert response.json()["id"] > 0
    assert response.json()["created_at"]
    assert "user_id" not in response.json()


async def test_create_entry_for_past_date(client: AsyncClient) -> None:
    identity = await create_user(client)
    exercise = await create_exercise_for(client, identity)
    past_date = date.today() - timedelta(days=30)

    entry = await create_entry_for(
        client,
        identity,
        int(exercise["id"]),
        performed_on=past_date,
    )

    assert entry["performed_on"] == past_date.isoformat()


async def test_cannot_create_entry_for_future_date(client: AsyncClient) -> None:
    identity = await create_user(client)
    exercise = await create_exercise_for(client, identity)
    user_today = get_user_today(DEFAULT_TIMEZONE)

    response = await client.post(
        "/exercise-entries",
        json={
            **identity,
            "exercise_id": exercise["id"],
            "reps": [10],
            "performed_on": (user_today + timedelta(days=1)).isoformat(),
        },
    )

    assert response.status_code == 422


async def test_get_exercise_history(client: AsyncClient) -> None:
    identity = await create_user(client)
    exercise = await create_exercise_for(client, identity)
    exercise_id = int(exercise["id"])
    older = await create_entry_for(
        client,
        identity,
        exercise_id,
        [8],
        date.today() - timedelta(days=1),
    )
    newer = await create_entry_for(client, identity, exercise_id, [10])

    response = await client.get(
        f"/exercises/{exercise_id}/entries",
        params=identity,
    )

    assert response.status_code == 200
    assert response.json() == [newer, older]


async def test_filter_history_from_date(client: AsyncClient) -> None:
    identity = await create_user(client)
    exercise = await create_exercise_for(client, identity)
    exercise_id = int(exercise["id"])
    dates = [date.today() - timedelta(days=days) for days in (10, 5, 1)]
    entries = [
        await create_entry_for(client, identity, exercise_id, [days], entry_date)
        for days, entry_date in zip((10, 5, 1), dates, strict=True)
    ]

    response = await client.get(
        f"/exercises/{exercise_id}/entries",
        params={**identity, "from": dates[1].isoformat()},
    )

    assert response.status_code == 200
    assert response.json() == [entries[2], entries[1]]


async def test_filter_history_to_date(client: AsyncClient) -> None:
    identity = await create_user(client)
    exercise = await create_exercise_for(client, identity)
    exercise_id = int(exercise["id"])
    dates = [date.today() - timedelta(days=days) for days in (10, 5, 1)]
    entries = [
        await create_entry_for(client, identity, exercise_id, [days], entry_date)
        for days, entry_date in zip((10, 5, 1), dates, strict=True)
    ]

    response = await client.get(
        f"/exercises/{exercise_id}/entries",
        params={**identity, "to": dates[1].isoformat()},
    )

    assert response.status_code == 200
    assert response.json() == [entries[1], entries[0]]


async def test_history_sorting_uses_date_then_created_at(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    identity = await create_user(client)
    exercise = await create_exercise_for(client, identity)
    exercise_id = int(exercise["id"])
    old_date = date.today() - timedelta(days=1)
    old = await create_entry_for(client, identity, exercise_id, [7], old_date)
    first = await create_entry_for(client, identity, exercise_id, [8])
    second = await create_entry_for(client, identity, exercise_id, [9])

    async with db_session.begin():
        first_model = await db_session.get(ExerciseEntry, first["id"])
        second_model = await db_session.get(ExerciseEntry, second["id"])
        assert first_model is not None
        assert second_model is not None
        first_model.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        second_model.created_at = datetime(2026, 1, 2, tzinfo=timezone.utc)

    response = await client.get(
        f"/exercises/{exercise_id}/entries",
        params=identity,
    )

    assert response.status_code == 200
    assert [entry["id"] for entry in response.json()] == [
        second["id"],
        first["id"],
        old["id"],
    ]


async def test_update_entry_reps(client: AsyncClient) -> None:
    identity = await create_user(client)
    exercise = await create_exercise_for(client, identity)
    entry = await create_entry_for(client, identity, int(exercise["id"]))

    response = await client.patch(
        f"/exercise-entries/{entry['id']}",
        json={**identity, "reps": [12, 11, 10]},
    )

    assert response.status_code == 200
    assert response.json()["reps"] == [12, 11, 10]


async def test_update_entry_performed_on(client: AsyncClient) -> None:
    identity = await create_user(client)
    exercise = await create_exercise_for(client, identity)
    entry = await create_entry_for(client, identity, int(exercise["id"]))
    new_date = date.today() - timedelta(days=7)

    response = await client.patch(
        f"/exercise-entries/{entry['id']}",
        json={**identity, "performed_on": new_date.isoformat()},
    )

    assert response.status_code == 200
    assert response.json()["performed_on"] == new_date.isoformat()


async def test_delete_entry_physically(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    identity = await create_user(client)
    exercise = await create_exercise_for(client, identity)
    entry = await create_entry_for(client, identity, int(exercise["id"]))

    response = await client.delete(
        f"/exercise-entries/{entry['id']}",
        params=identity,
    )

    assert response.status_code == 204
    assert response.content == b""
    assert await db_session.scalar(
        select(ExerciseEntry).where(ExerciseEntry.id == entry["id"])
    ) is None


async def test_cannot_access_another_users_entry(client: AsyncClient) -> None:
    owner = await create_user(client)
    other = await create_user(client)
    exercise = await create_exercise_for(client, owner)
    exercise_id = int(exercise["id"])
    entry = await create_entry_for(client, owner, exercise_id)

    history_response = await client.get(
        f"/exercises/{exercise_id}/entries",
        params=other,
    )
    patch_response = await client.patch(
        f"/exercise-entries/{entry['id']}",
        json={**other, "reps": [99]},
    )
    delete_response = await client.delete(
        f"/exercise-entries/{entry['id']}",
        params=other,
    )

    assert [
        history_response.status_code,
        patch_response.status_code,
        delete_response.status_code,
    ] == [404, 404, 404]


async def test_cannot_create_entry_for_another_users_exercise(
    client: AsyncClient,
) -> None:
    owner = await create_user(client)
    other = await create_user(client)
    exercise = await create_exercise_for(client, owner)

    response = await client.post(
        "/exercise-entries",
        json={
            **other,
            "exercise_id": exercise["id"],
            "reps": [10],
            "performed_on": date.today().isoformat(),
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Exercise not found"}


async def test_cannot_create_entry_for_archived_exercise(
    client: AsyncClient,
) -> None:
    identity = await create_user(client)
    exercise = await create_exercise_for(client, identity)
    await client.delete(f"/exercises/{exercise['id']}", params=identity)

    response = await client.post(
        "/exercise-entries",
        json={
            **identity,
            "exercise_id": exercise["id"],
            "reps": [10],
            "performed_on": date.today().isoformat(),
        },
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Exercise is archived"}


async def test_banned_user_receives_forbidden_for_entry_operations(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    identity = identity_payload()
    async with db_session.begin():
        user = User(is_banned=True)
        user.identities.append(UserIdentity(**identity))
        exercise = Exercise(name="Pull-ups")
        entry = ExerciseEntry(reps=[10], performed_on=date.today())
        exercise.exercise_entries.append(entry)
        user.exercises.append(exercise)
        db_session.add(user)
        await db_session.flush()
        exercise_id = exercise.id
        entry_id = entry.id

    responses = [
        await client.post(
            "/exercise-entries",
            json={
                **identity,
                "exercise_id": exercise_id,
                "reps": [10],
                "performed_on": date.today().isoformat(),
            },
        ),
        await client.get(
            f"/exercises/{exercise_id}/entries",
            params=identity,
        ),
        await client.patch(
            f"/exercise-entries/{entry_id}",
            json={**identity, "reps": [11]},
        ),
        await client.delete(
            f"/exercise-entries/{entry_id}",
            params=identity,
        ),
    ]

    assert [response.status_code for response in responses] == [403, 403, 403, 403]
    assert all(
        response.json() == {"detail": "User is banned"}
        for response in responses
    )


@pytest.mark.parametrize(
    "reps",
    [
        [],
        [0],
        [-1],
        [True],
        [MAX_REPETITIONS_PER_SET + 1],
        [1] * (MAX_SETS_PER_ENTRY + 1),
    ],
)
async def test_reps_validation(client: AsyncClient, reps: list[object]) -> None:
    identity = await create_user(client)
    exercise = await create_exercise_for(client, identity)

    response = await client.post(
        "/exercise-entries",
        json={
            **identity,
            "exercise_id": exercise["id"],
            "reps": reps,
            "performed_on": date.today().isoformat(),
        },
    )

    assert response.status_code == 422


async def test_history_limit_and_offset(client: AsyncClient) -> None:
    identity = await create_user(client)
    exercise = await create_exercise_for(client, identity)
    exercise_id = int(exercise["id"])
    entries = [
        await create_entry_for(
            client,
            identity,
            exercise_id,
            [index],
            date.today() - timedelta(days=index),
        )
        for index in range(1, 4)
    ]

    response = await client.get(
        f"/exercises/{exercise_id}/entries",
        params={**identity, "limit": 1, "offset": 1},
    )
    excessive_limit_response = await client.get(
        f"/exercises/{exercise_id}/entries",
        params={**identity, "limit": 101},
    )

    assert response.status_code == 200
    assert response.json() == [entries[1]]
    assert excessive_limit_response.status_code == 422
