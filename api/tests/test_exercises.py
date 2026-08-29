from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.models import Exercise, User, UserIdentity


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
    name: str = "Pull-ups",
) -> dict[str, object]:
    response = await client.post(
        "/exercises",
        json={**identity, "name": name},
    )
    assert response.status_code == 201
    return response.json()


async def test_create_exercise(
    client: AsyncClient,
) -> None:
    identity = await create_user(client)

    response = await client.post(
        "/exercises",
        json={**identity, "name": "  Pull-ups  "},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["name"] == "Pull-ups"
    assert body["position"] == 0
    assert body["is_archived"] is False
    assert body["created_at"]
    assert "user_id" not in body


@pytest.mark.parametrize("duplicate", ["Pull-ups", " pull-ups ", "PULL-UPS"])
async def test_duplicate_active_exercise_name_returns_conflict(
    client: AsyncClient,
    duplicate: str,
) -> None:
    identity = await create_user(client)
    original = await create_exercise_for(client, identity, "Pull-ups")

    response = await client.post(
        "/exercises",
        json={**identity, "name": duplicate},
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "An active exercise with this name already exists"
    }
    assert (await client.get("/exercises", params=identity)).json() == [original]


async def test_distinct_normalized_exercise_names_are_allowed(
    client: AsyncClient,
) -> None:
    identity = await create_user(client)

    first = await create_exercise_for(client, identity, "Pull-ups 1")
    second = await create_exercise_for(client, identity, "Pull-ups 2")

    assert first["id"] != second["id"]


async def test_archived_name_does_not_block_new_active_exercise(
    client: AsyncClient,
) -> None:
    identity = await create_user(client)
    archived = await create_exercise_for(client, identity, "Pull-ups")
    assert (
        await client.delete(f"/exercises/{archived['id']}", params=identity)
    ).status_code == 204

    response = await client.post(
        "/exercises",
        json={**identity, "name": " pull-UPS "},
    )

    assert response.status_code == 201
    assert response.json()["name"] == "pull-UPS"


async def test_get_exercises(
    client: AsyncClient,
) -> None:
    identity = await create_user(client)
    first = await create_exercise_for(client, identity, "Pull-ups")
    second = await create_exercise_for(client, identity, "Squats")

    response = await client.get("/exercises", params=identity)

    assert response.status_code == 200
    assert response.json() == [first, second]


async def test_exercises_are_isolated_by_user(
    client: AsyncClient,
) -> None:
    first_identity = await create_user(client)
    second_identity = await create_user(client)
    first_exercise = await create_exercise_for(client, first_identity)
    await create_exercise_for(client, second_identity, "Squats")

    response = await client.get("/exercises", params=first_identity)

    assert response.status_code == 200
    assert response.json() == [first_exercise]


async def test_rename_exercise(
    client: AsyncClient,
) -> None:
    identity = await create_user(client)
    exercise = await create_exercise_for(client, identity)

    response = await client.patch(
        f"/exercises/{exercise['id']}",
        json={**identity, "name": "  Chin-ups  "},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Chin-ups"


async def test_cannot_rename_another_users_exercise(
    client: AsyncClient,
) -> None:
    owner_identity = await create_user(client)
    other_identity = await create_user(client)
    exercise = await create_exercise_for(client, owner_identity)

    response = await client.patch(
        f"/exercises/{exercise['id']}",
        json={**other_identity, "name": "Stolen exercise"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Exercise not found"}
    owner_response = await client.get("/exercises", params=owner_identity)
    assert owner_response.json()[0]["name"] == "Pull-ups"


async def test_archive_exercise_keeps_database_row(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    identity = await create_user(client)
    exercise = await create_exercise_for(client, identity)

    response = await client.delete(
        f"/exercises/{exercise['id']}",
        params=identity,
    )

    assert response.status_code == 204
    assert response.content == b""
    stored_exercise = await db_session.scalar(
        select(Exercise).where(Exercise.id == exercise["id"])
    )
    assert stored_exercise is not None
    assert stored_exercise.is_archived is True


async def test_archived_exercise_is_not_returned_by_get(
    client: AsyncClient,
) -> None:
    identity = await create_user(client)
    exercise = await create_exercise_for(client, identity)
    await client.delete(f"/exercises/{exercise['id']}", params=identity)

    response = await client.get("/exercises", params=identity)

    assert response.status_code == 200
    assert response.json() == []


async def test_banned_user_receives_forbidden_for_all_operations(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    identity = identity_payload()
    async with db_session.begin():
        user = User(is_banned=True)
        user.identities.append(UserIdentity(**identity))
        exercise = Exercise(name="Pull-ups")
        user.exercises.append(exercise)
        db_session.add(user)
        await db_session.flush()
        exercise_id = exercise.id

    responses = [
        await client.get("/exercises", params=identity),
        await client.post(
            "/exercises",
            json={**identity, "name": "Squats"},
        ),
        await client.patch(
            f"/exercises/{exercise_id}",
            json={**identity, "name": "Chin-ups"},
        ),
        await client.delete(f"/exercises/{exercise_id}", params=identity),
    ]

    assert [response.status_code for response in responses] == [403, 403, 403, 403]
    assert all(
        response.json() == {"detail": "User is banned"}
        for response in responses
    )


async def test_unknown_identity_returns_not_found(
    client: AsyncClient,
) -> None:
    identity = identity_payload()

    response = await client.get("/exercises", params=identity)

    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}


@pytest.mark.parametrize("name", ["   ", "x" * 256])
async def test_exercise_name_is_validated(
    client: AsyncClient,
    name: str,
) -> None:
    identity = await create_user(client)

    response = await client.post(
        "/exercises",
        json={**identity, "name": name},
    )

    assert response.status_code == 422
