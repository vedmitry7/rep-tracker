import asyncio
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.db.session import async_session_factory
from api.app.main import app
from api.app.models.user import User
from api.app.models.user_identity import UserIdentity


pytestmark = pytest.mark.asyncio


def identity_payload() -> dict[str, str]:
    return {
        "provider": "test",
        "external_id": str(uuid4()),
    }


async def identity_count(
    session: AsyncSession,
    payload: dict[str, str],
) -> int:
    statement = (
        select(func.count())
        .select_from(UserIdentity)
        .where(
            UserIdentity.provider == payload["provider"],
            UserIdentity.external_id == payload["external_id"],
        )
    )
    return await session.scalar(statement) or 0


async def test_first_request_creates_user(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    payload = identity_payload()

    response = await client.post("/users/resolve", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["created_at"]
    assert body["is_banned"] is False
    assert body["timezone"] == "Europe/Moscow"
    assert body["language"] == "en"
    assert await identity_count(db_session, payload) == 1


async def test_repeated_request_returns_same_user(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    payload = identity_payload()

    first_response = await client.post("/users/resolve", json=payload)
    second_response = await client.post("/users/resolve", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 200
    assert second_response.json()["id"] == first_response.json()["id"]
    assert await identity_count(db_session, payload) == 1


async def test_new_user_gets_requested_default_timezone(client: AsyncClient) -> None:
    payload = {**identity_payload(), "default_timezone": "Europe/Madrid"}

    response = await client.post("/users/resolve", json=payload)

    assert response.status_code == 201
    assert response.json()["timezone"] == "Europe/Madrid"


async def test_repeated_resolve_does_not_change_timezone(client: AsyncClient) -> None:
    identity = identity_payload()
    first = await client.post(
        "/users/resolve",
        json={**identity, "default_timezone": "Europe/Madrid"},
    )
    second = await client.post(
        "/users/resolve",
        json={**identity, "default_timezone": "Asia/Tokyo"},
    )

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["timezone"] == "Europe/Madrid"


@pytest.mark.parametrize(
    ("default_language", "expected"),
    [("ru", "ru"), ("en", "en"), ("es", "en")],
)
async def test_new_user_language_with_fallback(
    client: AsyncClient,
    default_language: str,
    expected: str,
) -> None:
    response = await client.post(
        "/users/resolve",
        json={**identity_payload(), "default_language": default_language},
    )

    assert response.status_code == 201
    assert response.json()["language"] == expected


async def test_repeated_resolve_does_not_change_language(client: AsyncClient) -> None:
    identity = identity_payload()
    first = await client.post(
        "/users/resolve",
        json={**identity, "default_language": "ru"},
    )
    second = await client.post(
        "/users/resolve",
        json={**identity, "default_language": "en"},
    )

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["language"] == "ru"


async def test_resolve_rejects_invalid_timezone(client: AsyncClient) -> None:
    response = await client.post(
        "/users/resolve",
        json={**identity_payload(), "default_timezone": "UTC+3"},
    )

    assert response.status_code == 422


async def test_get_and_update_user_settings(client: AsyncClient) -> None:
    identity = identity_payload()
    await client.post(
        "/users/resolve",
        json={**identity, "default_timezone": "Europe/Moscow"},
    )

    get_response = await client.get("/users/settings", params=identity)
    patch_response = await client.patch(
        "/users/settings",
        json={**identity, "timezone": "Europe/Madrid"},
    )
    persisted_response = await client.get("/users/settings", params=identity)

    assert get_response.status_code == 200
    assert get_response.json()["timezone"] == "Europe/Moscow"
    assert get_response.json()["today"]
    assert get_response.json()["language"] == "en"
    assert patch_response.status_code == 200
    assert patch_response.json()["timezone"] == "Europe/Madrid"
    assert persisted_response.json()["timezone"] == "Europe/Madrid"


async def test_settings_can_update_language_both_directions(
    client: AsyncClient,
) -> None:
    identity = identity_payload()
    await client.post(
        "/users/resolve",
        json={**identity, "default_language": "ru"},
    )

    english = await client.patch(
        "/users/settings",
        json={**identity, "language": "en"},
    )
    russian = await client.patch(
        "/users/settings",
        json={**identity, "language": "ru"},
    )

    assert english.status_code == 200
    assert english.json()["language"] == "en"
    assert russian.status_code == 200
    assert russian.json()["language"] == "ru"
    assert russian.json()["timezone"] == "Europe/Moscow"


async def test_settings_reject_invalid_language(client: AsyncClient) -> None:
    identity = identity_payload()
    await client.post("/users/resolve", json=identity)

    response = await client.patch(
        "/users/settings",
        json={**identity, "language": "de"},
    )

    assert response.status_code == 422
    assert "language" in response.text


async def test_settings_reject_invalid_timezone(client: AsyncClient) -> None:
    identity = identity_payload()
    await client.post("/users/resolve", json=identity)

    response = await client.patch(
        "/users/settings",
        json={**identity, "timezone": "Europe/Definitely_Not_A_Zone"},
    )

    assert response.status_code == 422


async def test_settings_unknown_user_returns_not_found(client: AsyncClient) -> None:
    identity = identity_payload()

    get_response = await client.get("/users/settings", params=identity)
    patch_response = await client.patch(
        "/users/settings",
        json={**identity, "timezone": "Europe/Madrid"},
    )

    assert get_response.status_code == 404
    assert patch_response.status_code == 404


async def test_banned_user_cannot_access_settings(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    identity = identity_payload()
    async with db_session.begin():
        user = User(is_banned=True, timezone="Europe/Moscow")
        user.identities.append(UserIdentity(**identity))
        db_session.add(user)

    get_response = await client.get("/users/settings", params=identity)
    patch_response = await client.patch(
        "/users/settings",
        json={**identity, "timezone": "Europe/Madrid"},
    )

    assert get_response.status_code == 403
    assert patch_response.status_code == 403


async def test_banned_user_receives_forbidden(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    payload = identity_payload()
    async with db_session.begin():
        user = User(is_banned=True)
        user.identities.append(UserIdentity(**payload))
        db_session.add(user)

    response = await client.post("/users/resolve", json=payload)

    assert response.status_code == 403
    assert response.json() == {"detail": "User is banned"}


async def test_concurrent_requests_do_not_create_duplicate_identity() -> None:
    payload = identity_payload()

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as concurrent_client:
            responses = await asyncio.gather(
                concurrent_client.post("/users/resolve", json=payload),
                concurrent_client.post("/users/resolve", json=payload),
            )

        assert sorted(response.status_code for response in responses) == [200, 201]
        assert responses[0].json()["id"] == responses[1].json()["id"]

        async with async_session_factory() as session:
            assert await identity_count(session, payload) == 1
    finally:
        async with async_session_factory.begin() as session:
            user_ids = select(UserIdentity.user_id).where(
                UserIdentity.provider == payload["provider"],
                UserIdentity.external_id == payload["external_id"],
            )
            await session.execute(delete(User).where(User.id.in_(user_ids)))
