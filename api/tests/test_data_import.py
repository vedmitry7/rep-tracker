from datetime import date, timedelta
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
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


def document(*exercises: dict[str, object]) -> dict[str, object]:
    return {"version": 1, "exercises": list(exercises)}


def imported_exercise(
    name: str = "Pull-ups",
    *,
    entries: list[list[int]] | None = None,
    performed_on: str = "2026-08-01",
) -> dict[str, object]:
    return {
        "name": name,
        "days": [
            {
                "date": performed_on,
                "entries": (
                    [[10], [8], [10, 10, 10, 8]]
                    if entries is None
                    else entries
                ),
            }
        ],
    }


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
) -> None:
    response = await client.post(
        "/exercise-entries",
        json={
            **identity,
            "exercise_id": exercise_id,
            "reps": reps,
            "performed_on": "2026-07-01",
        },
    )
    assert response.status_code == 201


async def test_preview_reports_counts_matches_and_writes_nothing(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    identity = await create_user(client)
    existing = await create_exercise(client, identity, "Pull-ups")
    payload = document(
        imported_exercise("  PULL-UPS  "),
        {
            "name": "Squats",
            "days": [
                {"date": "2026-08-01", "entries": [[5]]},
                {"date": "2026-08-02", "entries": [[6, 7]]},
            ],
        },
    )

    response = await client.post(
        "/imports/preview", json={**identity, "document": payload}
    )

    assert response.status_code == 200
    assert response.json() == {
        "exercises_count": 2,
        "entries_count": 5,
        "total_reps": 74,
        "date_from": "2026-08-01",
        "date_to": "2026-08-02",
        "new_exercises": ["Squats"],
        "existing_exercises": ["Pull-ups"],
    }
    assert (await client.get("/exercises", params=identity)).json() == [existing]
    assert await db_session.scalar(
        select(func.count(ExerciseEntry.id)).where(
            ExerciseEntry.exercise_id == existing["id"]
        )
    ) == 0


async def test_merge_creates_entries_with_correct_day_and_entry_boundaries(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    identity = await create_user(client)
    payload = document(imported_exercise())

    response = await client.post(
        "/imports", json={**identity, "document": payload, "strategy": "merge"}
    )

    assert response.status_code == 201
    assert response.json()["exercises_created"] == 1
    exercise = await db_session.scalar(
        select(Exercise).where(Exercise.name == "Pull-ups")
    )
    assert exercise is not None
    entries = list(
        (
            await db_session.scalars(
                select(ExerciseEntry)
                .where(ExerciseEntry.exercise_id == exercise.id)
                .order_by(ExerciseEntry.id)
            )
        ).all()
    )
    assert [entry.reps for entry in entries] == [[10], [8], [10, 10, 10, 8]]
    assert {entry.performed_on for entry in entries} == {date(2026, 8, 1)}


async def test_repeated_merge_keeps_existing_and_allows_duplicates(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    identity = await create_user(client)
    exercise = await create_exercise(client, identity, "Pull-ups")
    await add_entry(client, identity, int(exercise["id"]), [3])
    payload = document(imported_exercise(" pull-UPS ", entries=[[10]]))

    for _ in range(2):
        response = await client.post(
            "/imports",
            json={**identity, "document": payload, "strategy": "merge"},
        )
        assert response.status_code == 201

    reps = list(
        (
            await db_session.scalars(
                select(ExerciseEntry.reps)
                .where(ExerciseEntry.exercise_id == exercise["id"])
                .order_by(ExerciseEntry.id)
            )
        ).all()
    )
    assert reps == [[3], [10], [10]]


async def test_replace_keeps_exercise_deletes_its_history_and_leaves_others(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    identity = await create_user(client)
    pull_ups = await create_exercise(client, identity, "Pull-ups")
    squats = await create_exercise(client, identity, "Squats")
    await add_entry(client, identity, int(pull_ups["id"]), [3])
    await add_entry(client, identity, int(squats["id"]), [20])

    response = await client.post(
        "/imports",
        json={
            **identity,
            "document": document(imported_exercise(entries=[[11, 9]])),
            "strategy": "replace",
        },
    )

    assert response.status_code == 201
    assert response.json()["exercises_created"] == 0
    assert response.json()["existing_exercises_updated"] == 1
    assert await db_session.get(Exercise, pull_ups["id"]) is not None
    rows = (
        await db_session.execute(
            select(ExerciseEntry.exercise_id, ExerciseEntry.reps)
            .where(ExerciseEntry.exercise_id.in_([pull_ups["id"], squats["id"]]))
            .order_by(ExerciseEntry.exercise_id)
        )
    ).all()
    assert rows == [(pull_ups["id"], [11, 9]), (squats["id"], [20])]


@pytest.mark.parametrize(
    "bad_document",
    [
        {"version": 2, "exercises": [imported_exercise()]},
        document(imported_exercise(entries=[])),
        document(imported_exercise(entries=[[0]])),
        document(imported_exercise(entries=[[1.5]])),
        document(imported_exercise(performed_on="01.08.2026")),
        document(imported_exercise(performed_on="2026-08-01T00:00:00")),
    ],
)
async def test_invalid_document_is_rejected_atomically(
    client: AsyncClient, db_session: AsyncSession, bad_document: dict[str, object]
) -> None:
    identity = await create_user(client)
    response = await client.post(
        "/imports",
        json={**identity, "document": bad_document, "strategy": "merge"},
    )
    assert response.status_code == 422
    assert (await client.get("/exercises", params=identity)).json() == []


async def test_import_rejects_duplicate_normalized_exercise_names(
    client: AsyncClient,
) -> None:
    identity = await create_user(client)
    payload = document(
        imported_exercise("Pull-ups"),
        imported_exercise("  PULL-UPS  "),
    )

    response = await client.post(
        "/imports/preview",
        json={**identity, "document": payload},
    )

    assert response.status_code == 422
    assert "duplicate normalized exercise names" in str(response.json())
    assert (await client.get("/exercises", params=identity)).json() == []


async def test_future_date_uses_user_timezone_and_writes_nothing(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    identity = await create_user(client)
    future = (date.today() + timedelta(days=2)).isoformat()
    response = await client.post(
        "/imports",
        json={
            **identity,
            "document": document(imported_exercise(performed_on=future)),
            "strategy": "merge",
        },
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Import contains a future date"}
    assert (await client.get("/exercises", params=identity)).json() == []


async def test_import_is_scoped_to_identity_and_banned_users_are_rejected(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    owner = await create_user(client)
    other = await create_user(client)
    exercise = await create_exercise(client, owner, "Pull-ups")
    payload = document(imported_exercise(entries=[[10]]))

    response = await client.post(
        "/imports", json={**other, "document": payload, "strategy": "replace"}
    )
    assert response.status_code == 201
    assert response.json()["exercises_created"] == 1

    banned_identity = identity_payload()
    async with db_session.begin():
        banned = User(is_banned=True)
        banned.identities.append(UserIdentity(**banned_identity))
        db_session.add(banned)
    banned_response = await client.post(
        "/imports/preview",
        json={**banned_identity, "document": payload},
    )
    assert banned_response.status_code == 403
    owner_entries = await client.get(
        f"/exercises/{exercise['id']}/entries", params=owner
    )
    assert owner_entries.status_code == 200
    assert owner_entries.json() == []
