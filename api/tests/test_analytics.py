from datetime import date
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.models import User, UserEvent
from api.app.models.user_identity import UserIdentity


pytestmark = pytest.mark.asyncio


def identity() -> dict[str, str]:
    return {"provider": "test", "external_id": str(uuid4())}


async def test_analytics_records_product_events_and_returns_summary(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    before = (await client.get("/analytics/summary", params={"days": 7})).json()
    first_identity = identity()
    second_identity = identity()
    await client.post("/users/resolve", json=first_identity)
    await client.post("/users/resolve", json=second_identity)

    exercise_response = await client.post(
        "/exercises", json={**first_identity, "name": "Push-ups"}
    )
    exercise_id = exercise_response.json()["id"]
    entry_response = await client.post(
        "/exercise-entries",
        json={
            **first_identity,
            "exercise_id": exercise_id,
            "reps": [10, 12],
            "performed_on": date.today().isoformat(),
        },
    )
    assert entry_response.status_code == 201

    for event_type in ("stats_opened", "weekly_report_opened"):
        response = await client.post(
            "/analytics/events", json={**first_identity, "event_type": event_type}
        )
        assert response.status_code == 204

    summary_response = await client.get("/analytics/summary", params={"days": 7})

    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["total_users"] == before["total_users"] + 2
    assert summary["new_users"] == before["new_users"] + 2
    assert summary["active_users"] == before["active_users"] + 2
    assert summary["activated_new_users"] == before["activated_new_users"] + 1
    assert summary["result_entries"] == before["result_entries"] + 1
    assert summary["feature_opens"]["stats_opened"] == (
        before["feature_opens"]["stats_opened"] + 1
    )
    assert summary["feature_opens"]["weekly_report_opened"] == (
        before["feature_opens"]["weekly_report_opened"] + 1
    )
    assert summary["feature_opens"]["import_used"] == before["feature_opens"]["import_used"]
    assert summary["feature_opens"]["export_used"] == before["feature_opens"]["export_used"]
    assert summary["locales"]["en"] == before["locales"].get("en", 0) + 2

    user = await db_session.scalar(
        select(User)
        .join(UserIdentity)
        .where(UserIdentity.external_id == first_identity["external_id"])
    )
    assert user is not None
    assert user.last_active_at is not None
    events = list(
        (
            await db_session.scalars(
                select(UserEvent.event_type)
                .where(UserEvent.user_id == user.id)
                .order_by(UserEvent.id)
            )
        ).all()
    )
    assert events == [
        "start",
        "exercise_created",
        "result_added",
        "stats_opened",
        "weekly_report_opened",
    ]


async def test_analytics_rejects_unknown_period(client: AsyncClient) -> None:
    response = await client.get("/analytics/summary", params={"days": 14})

    assert response.status_code == 422
