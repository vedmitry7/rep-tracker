from uuid import uuid4

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


def identity_payload() -> dict[str, str]:
    return {"provider": "test", "external_id": str(uuid4())}


async def create_user(client: AsyncClient) -> dict[str, str]:
    identity = identity_payload()
    response = await client.post("/users/resolve", json=identity)
    assert response.status_code == 201
    return identity


async def create_exercise(
    client: AsyncClient, identity: dict[str, str], name: str
) -> dict[str, object]:
    response = await client.post("/exercises", json={**identity, "name": name})
    assert response.status_code == 201
    return response.json()


async def add_entry(
    client: AsyncClient,
    identity: dict[str, str],
    exercise_id: int,
    reps: list[int],
    performed_on: str,
) -> None:
    response = await client.post(
        "/exercise-entries",
        json={
            **identity,
            "exercise_id": exercise_id,
            "reps": reps,
            "performed_on": performed_on,
        },
    )
    assert response.status_code == 201


async def test_export_builds_import_document_and_keeps_empty_exercises(
    client: AsyncClient,
) -> None:
    identity = await create_user(client)
    pull_ups = await create_exercise(client, identity, "Pull-ups")
    plank = await create_exercise(client, identity, "Plank")
    await add_entry(client, identity, int(pull_ups["id"]), [10], "2026-08-01")
    await add_entry(client, identity, int(pull_ups["id"]), [8, 7], "2026-08-01")
    await add_entry(client, identity, int(pull_ups["id"]), [6], "2026-08-02")

    response = await client.post(
        "/exports",
        json={**identity, "exercise_ids": [int(plank["id"]), int(pull_ups["id"])]},
    )

    assert response.status_code == 200
    assert response.json() == {
        "version": 1,
        "exercises": [
            {
                "name": "Pull-ups",
                "days": [
                    {"date": "2026-08-01", "entries": [[10], [8, 7]]},
                    {"date": "2026-08-02", "entries": [[6]]},
                ],
            },
            {"name": "Plank", "days": []},
        ],
    }

    preview = await client.post(
        "/imports/preview", json={**identity, "document": response.json()}
    )
    assert preview.status_code == 200
    assert preview.json()["entries_count"] == 3


async def test_export_rejects_exercises_not_owned_by_user(
    client: AsyncClient,
) -> None:
    owner = await create_user(client)
    other = await create_user(client)
    exercise = await create_exercise(client, owner, "Pull-ups")

    response = await client.post(
        "/exports", json={**other, "exercise_ids": [int(exercise["id"])]}
    )

    assert response.status_code == 404
